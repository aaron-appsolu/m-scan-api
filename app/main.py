from hashlib import md5
from typing import Annotated

from fastapi import FastAPI, Query

from app.mongo import route_types, routes
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
    return [{**d.get('vpl'), 'selected': True} for d in result]


@app.get("/routes")
async def get_vpl(vpl_uides: Annotated[list, Query()] = []):
    r = list(routes.find({'vpl_uide': {'$in': vpl_uides}}, {'_id': 0, 'route_type': 0}).limit(100))
    return r


@app.get("/route_types")
async def get_route_types():
    return list(route_types.find({}, {'_id': 0}))
