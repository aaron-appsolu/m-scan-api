from typing import List
from fastapi import FastAPI
from app.mongo import routeTypes, routes, ppl
from app.neo import execute_query
from fastapi.middleware.cors import CORSMiddleware
from app.structure.nodes import PPL

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


@app.get("/vpl")
async def get_vpl():
    result = execute_query('MATCH (vpl:VPL) RETURN vpl')
    return [{**d.get('vpl'), 'selected': False} for d in result]


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
                        '_id': 0
                    }}
                ],
                'as': 'routes'
            }
        },
        {'$project': {'_id': 0}}
    ]

    # res = ppl.find({'vpl_uide': {'$in': vpl_uides}}, {'_id': 0})
    res = ppl.aggregate(pipeline)

    return [{**d, 'selected': False} for d in res]


@app.post("/ppl/update")
async def get_vpl(changes: List[PPL]):
    return None


@app.get("/routes")
async def get_vpl(vpl_uides: str):
    vpl_uides = vpl_uides.split(',')
    r = routes.find({'vpl_uide': {'$in': vpl_uides}}, {'_id': 0, 'features': 0})
    return list(r)


@app.get("/routes/features")
async def get_vpl(vpl_uide: str, ppl_uide: str, route_type: str):
    r = routes.find_one({'vpl_uide': vpl_uide, 'ppl_uide': ppl_uide, 'route_type': route_type},
                        {'_id': 0, 'features': 1})
    return r.get('features') or []


@app.get("/route_types")
async def get_route_types():
    return [{**d, 'selected': False} for d in routeTypes.find({}, {'_id': 0})]
