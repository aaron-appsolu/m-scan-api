from datetime import datetime
from typing import List, Any
from fastapi import FastAPI
from pymongo import UpdateOne
from pymongo.collection import Collection

from app.mongo import routeTypes, routes, ppl, vvm_observed, vvm_formatted
from app.neo import execute_query
from fastapi.middleware.cors import CORSMiddleware
from app.structure.nodes import PPL
from app.structure.types import VVMFormatted, VVMObserved

origins = [
    "https://m-scan-v2.made4it.com",
    "http://localhost:4200"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ppl")
async def get_vpl(vpl_uides: str):
    vpl_uides = vpl_uides.split(',')
    pipeline = [
        {'$match': {'vpl_uide': {'$in': vpl_uides}}},
        {
            '$lookup': {
                'from': 'routes',
                'let': {'uide': '$uide'},
                'pipeline': [
                    {'$match': {'$expr': {'$eq': ['$ppl_uide', '$$uide']}}},
                    {'$project': {
                        'total_distance': 1,
                        'total_duration': 1,
                        'route_type': 1,
                        'route_id': 1,
                        'features_zlib': 1,
                        '_id': 0
                    }}
                ],
                'as': 'routes'
            }
        },
        {'$addFields': {'lat': "$lat_jitter", 'lng': "$lng_jitter"}},
        {'$project': {'_id': 0, 'lat_jitter': 0, 'lng_jitter': 0}}
    ]

    # ppl.find({'vpl_uide': {'$in': vpl_uides}}, {'_id': 0})
    return [d for d in ppl.aggregate(pipeline)]


@app.get("/vvm")
async def get_vvm():
    o = list(vvm_observed.find({}, {'_id': 0}))
    f = list(vvm_formatted.find({}, {'_id': 0}))

    return {
        'obs': o,
        'rpt': [d for d in f if d['type'] == 'rpt'],
        'std': [d for d in f if d['type'] == 'std']
    }


@app.get("/vpl")
async def get_vpl():
    result = execute_query('MATCH (vpl:VPL) RETURN vpl')
    return [{**d.get('vpl')} for d in result]


def updater(col: Collection, changes: List[Any]):
    timestamp = datetime.now()
    operations = [UpdateOne({'uide': d.uide}, {'$set': {**d.model_dump(), 'lastEdited': timestamp}}) for d in changes]
    col.bulk_write(operations)


@app.post("/ppl/update")
async def get_vpl(changes: List[PPL]):
    return updater(ppl, changes)


@app.post("/vvm/update/formatted")
async def get_vpl(changes: List[VVMFormatted]):
    return updater(vvm_formatted, changes)


@app.post("/vvm/update/observed")
async def get_vpl(changes: List[VVMObserved]):
    return updater(vvm_observed, changes)


def flat_feat(res) -> List:
    return [d2 for r in res for d2 in r.get('features')]


@app.get("/routes/features/ppl/{ppl_uide}")
async def get_ppl_all_routes(ppl_uide: str):
    return flat_feat(routes.find({'ppl_uide': ppl_uide},
                                 {'_id': 0, 'features': 1}))


@app.get("/routes/features/ppl/{ppl_uide}/{route_type}")
async def get_ppl_route(ppl_uide: str, route_type: str):
    return flat_feat(routes.find({'ppl_uide': ppl_uide, 'route_type': route_type},
                                 {'_id': 0, 'features': 1}))


@app.get("/routes/features/vpl/{vpl_uide}")
async def get_vpl_all_routes(vpl_uide: str):
    return list(routes.find({'vpl_uide': vpl_uide},
                            {'_id': 0, 'features_zlib': 1, 'route_type': 1, 'vpl_uide': 1, 'ppl_uide': 1}))


@app.get("/routes/features/vpl/{vpl_uide}/{route_type}")
async def get_vpl_route(vpl_uide: str, route_type: str):
    return list(routes.find({'vpl_uide': vpl_uide, 'route_type': route_type},
                            {'_id': 0, 'features_zlib': 1, 'route_type': 1, 'vpl_uide': 1, 'ppl_uide': 1}))


@app.get("/route_types")
async def get_route_types():
    return [d for d in routeTypes.find({}, {'_id': 0})]
