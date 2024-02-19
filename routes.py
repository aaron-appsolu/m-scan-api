import json
from datetime import datetime
from typing import List

from neo4j import Record
from polyline import decode, encode

from geojson import Feature, LineString, Point, FeatureCollection
from neo4j.graph import Node as NeoNode, Relationship as NeoEdge
from pymongo import UpdateOne

from app.mongo import route_types, routes
from app.neo import execute_query
from helpers import chunks


def node(idx: int, t: str):
    return f'(v{idx}:{t})'


def edge(idx: int, t: str):
    return f'-[v{idx}:{t}]->'


for route_type in route_types.find({'active': True}):
    operations = []
    route: List[str] = route_type.get('route')
    if not route or not len(route) % 2:
        raise AttributeError

    match_statement = ''.join(edge(idx, d) if idx % 2 else node(idx, d) for idx, d in enumerate(route))
    variables = ','.join(f'v{idx}' for idx, d in enumerate(route))
    count_query = f"MATCH {match_statement} RETURN count(*)"
    count = execute_query(count_query)[0].get('count(*)')
    print(f"{count} items found for {route_type.get('internalLabel')}")
    query = f"MATCH {match_statement} RETURN {variables}"
    result: List[Record] = execute_query(query)

    for res_idx, res in enumerate(result):

        features = []
        total_duration = 0
        total_distance = 0
        ppl_uide = res.values()[0].get('uide')
        vpl_uide = res.values()[-1].get('uide')

        for r in res:
            geometry = None
            props = {
                'type': r.get('type')
            }
            if isinstance(r, NeoNode):
                geometry = Point(r.get('point'))
                # props.update()
            if isinstance(r, NeoEdge):
                total_duration += r.get('duration') or 0
                total_distance += r.get('distance') or 0
                polyline = decode(r.get('polyline'), geojson=True)
                geometry = LineString(polyline)
                props.update({
                    'duration': r.get('duration'),
                    'distance': r.get('distance'),
                    'type': r.get('type'),
                    'is_direct': len(polyline) == 2
                })

            assert geometry is not None
            assert props is not None

            feature = Feature(geometry=geometry, properties=props)
            features.append(feature)

        upsert = {
            'ppl_uide': ppl_uide,
            'vpl_uide': vpl_uide,
            'route_type': route_type.get('route_type')
        }
        doc = {
            '$set': {
                'features': features,
                'lastEdited': datetime.now(),
                'total_duration': total_duration,
                'total_distance': total_distance
            },
            '$setOnInsert': {
                **upsert,
                'created': datetime.now()
            }
        }
        operations.append(UpdateOne(upsert, doc, upsert=True))

    chunk_size = 5000
    chunked_list = chunks(operations, chunk_size)
    for idx, sub_list in enumerate(chunked_list):
        print(f"Creating {idx * chunk_size + len(sub_list)}/{len(operations)} "
              f"routes of type {route_type.get('internalLabel')}...")
        routes.bulk_write(sub_list, ordered=False)
