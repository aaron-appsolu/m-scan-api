from datetime import datetime
from typing import List, Any, Dict, Mapping, Sequence
from fastapi import FastAPI
from pydantic import ConfigDict
from pymongo import UpdateOne
from pymongo.collection import Collection

from app.mongo import routeTypes, routes, ppl, vvm_observed, vvm_formatted, icons
from app.neo import execute_query
from fastapi.middleware.cors import CORSMiddleware
from app.structure.nodes import PPL
from app.structure.types import VVMFormatted, VVMObserved, Route

origins = [
    "https://m-scan-v2.made4it.com",
    "http://localhost:4200"
]

# mypy ./app/main.py
# bandit?

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
    uides = vpl_uides.split(',')
    pipeline = [
        {'$match': {'vpl_uide': {'$in': uides}}},
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
                        'uide': 1,
                        'features_zlib': 1,
                        'excluded_from': 1,
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
async def update_ppl(changes: List[PPL]):
    return updater(ppl, changes)


class DecodedPPL(PPL):
    routes: List[Route]
    model_config = ConfigDict(extra='ignore')


@app.post("/route/update")
async def update_route(changes: List[DecodedPPL]):
    ppl_routes = [route for d in changes for route in d.routes]
    return updater(routes, ppl_routes)


@app.post("/vvm/update/formatted")
async def update_vvm_formatted(changes: List[VVMFormatted]):
    return updater(vvm_formatted, changes)


@app.post("/vvm/update/observed")
async def update_vvm_observed(changes: List[VVMObserved]):
    return updater(vvm_observed, changes)


@app.get("/route_types")
async def get_route_types():
    return [d for d in routeTypes.find({'active': True}, {'_id': 0})]


@app.get("/icons")
async def get_icons():
    return [d for d in icons.find({}, {'_id': 0})]
