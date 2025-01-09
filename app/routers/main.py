from datetime import datetime
from typing import List, Any
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import ConfigDict
from pymongo import UpdateOne, DeleteOne
from pymongo.collection import Collection
from starlette import status

from app.mongo import routeTypes, routes, ppl, vvm_observed, vvm_formatted, icons, rekenregels, languages, owners, \
    translation_fields
from app.neo import execute_query
from app.structure.nodes import PPL
from app.structure.types import VVMFormatted, VVMObserved, Route, Language

router = APIRouter()


@router.get("/rekenregels")
async def get_rekenregels(owner: str):
    return list(rekenregels.find({'owner': owner}, {'_id': 0}))


@router.get("/owners")
async def get_owners():
    return list(owners.find({}, {'_id': 0}))


@router.get("/languages")
async def get_languages():
    return list(languages.find({}, {'_id': 0}))


@router.get("/translation_fields")
async def get_languages():
    return list(translation_fields.find({}, {'_id': 0}))


@router.get("/ppl")
async def get_ppl(vpl_uides: str, owner: str):
    uides = vpl_uides.split(',')
    pipeline = [
        {'$match': {'vpl_uide': {'$in': uides}, 'owner': owner}},
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

    return [d for d in ppl.aggregate(pipeline)]


@router.get("/vvm")
async def get_vvm(owner: str):
    o = list(vvm_observed.find({'owner': owner}, {'_id': 0}))
    f = list(vvm_formatted.find({'owner': owner}, {'_id': 0}))

    return {
        'obs': o,
        'rpt': [d for d in f if d['type'] == 'rpt'],
        'std': [d for d in f if d['type'] == 'std']
    }


@router.get("/vpl")
async def get_vpl(owner: str):
    result = execute_query('MATCH (vpl:VPL {owner: $owner}) RETURN vpl', owner=owner)
    return [{**d.get('vpl')} for d in result]


def updater(col: Collection, changes: List[Any], keys: List[str]):
    timestamp = datetime.now()
    operations = [UpdateOne({k: getattr(d, k) for k in keys}, {'$set': {**d.model_dump(), 'lastEdited': timestamp}})
                  for d in changes]
    col.bulk_write(operations)


@router.post("/ppl/update")
async def update_ppl(changes: List[PPL]):
    return updater(ppl, changes, ['uide'])


class DecodedPPL(PPL):
    routes: List[Route]
    model_config = ConfigDict(extra='ignore')


@router.post("/route/update")
async def update_route(changes: List[DecodedPPL]):
    ppl_routes = [route for d in changes for route in d.routes]
    return updater(routes, ppl_routes, ['uide'])


@router.post("/vvm/update/formatted")
async def update_vvm_formatted(changes: List[VVMFormatted]):
    return updater(vvm_formatted, changes, ['uide', 'owner', 'type'])


@router.post("/vvm/combine/formatted")
async def combine_vvm_formatted(changes: List[VVMFormatted], owner: str):
    main_qry = {'owner': owner, 'type': 'std'}
    ref_vvm, *rem_vvm = changes
    count = rekenregels.count_documents(
        {'smartVvm.std': {'$in': [d.uide for d in rem_vvm]}, **main_qry})

    if count > 0:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT,
                            content={'reason': 'Data is used in rekenregel'})

    ops = [UpdateOne({'std_uide': d.uide, **main_qry}, {'$set': {'std_uide': ref_vvm.uide}}) for d in rem_vvm]
    vvm_observed.bulk_write(ops)
    vvm_formatted.delete_many({'uide': {'$in': [d.uide for d in rem_vvm]}, **main_qry})
    return list(vvm_formatted.find(main_qry, {'_id': 0}))


@router.post("/vvm/update/observed")
async def update_vvm_observed(changes: List[VVMObserved]):
    return updater(vvm_observed, changes, ['uide', 'owner', 'type'])


@router.post("/language/update")
async def update_ppl(changes: List[Language]):
    return updater(languages, changes, ['uide'])


@router.get("/route_types")
async def get_route_types(owner: str):
    return [d for d in routeTypes.find({'active': True}, {'_id': 0})]


@router.get("/icons")
async def get_icons(owner: str):
    return [d for d in icons.find({'owner': owner}, {'_id': 0})]
