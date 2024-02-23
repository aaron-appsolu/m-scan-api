from hashlib import md5
from typing import Annotated

from fastapi import FastAPI, Query

from app.mongo import routeTypes, routes
from app.neo import execute_query
from fastapi.middleware.cors import CORSMiddleware

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
