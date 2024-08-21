import base64
import json
import zlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List

from bson import ObjectId
from neo4j import Record
from app.helpers.google import decode
from geojson import Feature, LineString, Point
from neo4j.graph import Node as NeoNode, Relationship as NeoEdge
from pymongo import UpdateOne

from app.mongo import routeTypes, routes, ppl
from app.neo import execute_query
from app.structure.nodes import PPL


def node(idx: int, t: str):
    return f'(v{idx}:{t})'


def edge(idx: int, t: str):
    return f'-[v{idx}:{t}]->'


rt = [d for d in routeTypes.find({'active': True})]
ppls = [d for d in ppl.find({'_id': {'$gte': ObjectId('66bd0bddf73c0fca6ae43491')}}, {'uide': 1, 'vpl_uide': 1})]


def handle_ppl(ppl_idx: int, p: PPL):
    ppl_uide = p.get('uide')
    vpl_uide = p.get('vpl_uide')
    operations = []
    for route_type in rt:
        route: List[str] = route_type.get('route')
        if not route or not len(route) % 2:
            raise AttributeError

        match_statement = ''.join(edge(idx, d) if idx % 2 else node(idx, d) for idx, d in enumerate(route))
        match_statement = match_statement.replace('PPL', f"PPL {{uide: '{ppl_uide}'}}")
        match_statement = match_statement.replace('VPL', f"VPL {{uide: '{vpl_uide}'}}")
        # variables = ','.join(f'v{idx}' for idx, d in enumerate(route))
        # query = f"MATCH {match_statement} RETURN {variables}"
        query = f"MATCH {match_statement} RETURN *"
        result: List[Record] = execute_query(query)

        for res in result:
            features = []
            total_duration = 0
            total_distance = 0
            ppl_uide = res.values()[0].get('uide')
            vpl_uide = res.values()[-1].get('uide')

            for r in res:
                if isinstance(r, NeoNode):
                    features.append({
                        'props': {
                            'type': r.get('type')
                        },
                        'encoded': r.get('point'),
                        'type': 'P'
                    })
                if isinstance(r, NeoEdge):
                    total_duration += r.get('duration') or 0
                    total_distance += r.get('distance') or 0

                    features.append({
                        'props': {
                            'duration': r.get('duration'),
                            'distance': r.get('distance'),
                            'type': r.get('type')
                        },
                        'encoded': r.get('polyline'),
                        'type': 'L'
                    })

            compressed_bytes: bytes = zlib.compress(json.dumps(features).encode('utf-8'))
            base64_encoded_data = base64.b64encode(compressed_bytes).decode('utf-8')

            upsert = {
                'ppl_uide': ppl_uide,
                'vpl_uide': vpl_uide,
                'route_type': route_type.get('route_type')
            }
            doc = {
                '$set': {
                    'features_zlib': base64_encoded_data,
                    'route_id': route_type.get('id'),
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

    if len(operations) > 0:
        routes.bulk_write(operations, ordered=False)
        print(f"{ppl_idx + 1}/{len(ppls)}: routes added")
    else:
        print(f"{ppl_idx + 1}/{len(ppls)}: no routes")


#
# for ppl_idx, p in enumerate(ppls):
#     handle_ppl(ppl_idx, p)


with ThreadPoolExecutor(max_workers=75) as executor:
    # Submit tasks to the thread pool
    futures = [executor.submit(handle_ppl, ppl_idx, p) for ppl_idx, p in enumerate(ppls)]

    # Process the results as they complete
    for future in futures:
        future_res = future.result()

print('Done')
