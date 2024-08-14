from typing import List, Any

from pymongo import UpdateOne
from pymongo.collection import Collection

from app.neo import execute_query
from helpers import chunks
from structure.edges import Edge
from structure.nodes import Node, NodeTypes
from datetime import datetime

chunk_size = 10_000


def create_nodes_neo(nodes: List[Node]):
    if len(nodes) == 0:
        return
    t = nodes[0].type

    qry = f"""
    UNWIND $nodes AS d
    WITH d AS d, point({{latitude: d.lat, longitude: d.lng}}) AS pt
    MERGE (n:{t} {{uide: d.uide}})
    ON CREATE SET
        n = d,
        n.created = timestamp(),
        n.lastEdited = timestamp(),
        n.point = pt
    ON MATCH SET
        n = d,
        n.lastEdited = timestamp(),
        n.point = pt
    """

    chunked_list = chunks(nodes, chunk_size)
    for idx, sub_nodes in enumerate(chunked_list):
        print(f'(:{t}): Creating {idx * chunk_size + len(sub_nodes)}/{len(nodes)} nodes...')
        execute_query(qry, nodes=[d.dict() for d in sub_nodes])

    # print(f'Creating {len(nodes)} nodes of type {n0.type}...')
    # execute_query(qry, nodes=[d.dict() for d in nodes])


def create_nodes_mongo(nodes: List[Node], collection: Collection):
    timestamp = datetime.now()

    operations = [UpdateOne({'uide': d.uide}, {
        '$setOnInsert': {'created': timestamp},
        '$set': {**d.dict(), 'lastEdited': timestamp}
    }, upsert=True) for d in nodes]

    chunked_list = chunks(operations, chunk_size)
    for idx, sub_operations in enumerate(chunked_list):
        print(f'Creating {idx * chunk_size + len(sub_operations)}/{len(nodes)} nodes...')
        collection.bulk_write(sub_operations, ordered=False)


def create_edges(edges: List[Edge]):
    if len(edges) == 0:
        return
    e0 = edges[0]
    # model_fields = e0.model_fields
    # r = ',\n'.join([f"e.{k} = d.{k}" for k in model_fields.keys()])
    qry = f"""
    UNWIND $edges AS d
    MATCH (a:{e0.type_a} {{uide: d.uide_a}})
    MATCH (b:{e0.type_b} {{uide: d.uide_b}})
    MERGE (a)-[e:{e0.type} {{uide_a: d.uide_a, uide_b: d.uide_b}}]->(b)
    ON CREATE SET
        e = d,
        e.created = timestamp(),
        e.lastEdited = timestamp()
    ON MATCH SET
        e = d,
        e.lastEdited = timestamp()
    """

    chunked_list = chunks(edges, chunk_size)
    for idx, sub_edges in enumerate(chunked_list):
        print(f'(:{e0.type_a})-[:{e0.type}]->({e0.type_b}): '
              f'Creating {idx * chunk_size + len(sub_edges)}/{len(edges)} edges...')
        execute_query(qry, edges=[d.dict() for d in sub_edges])

    # print(f'Creating {len(edges)} edges of type {e0.type}...')
    # execute_query(qry, edges=[d.dict() for d in edges])
