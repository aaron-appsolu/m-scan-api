from time import sleep
from typing import List
from neo4j import Record
from neo4j.graph import Relationship
from geojson import LineString, FeatureCollection, Feature, dumps as geodumps
from app.neo import execute_query
from app.mongo import vpl_old, ppl_old, gamma, via_old, alfa, beta, ppl
from structure.nodes import PPL, VPL, VIA, NodeTypes, Node
from structure.graph_types import create_edges, create_nodes_neo, create_nodes_mongo
from structure.edges import GammaWalk, GammaCar, GammaTransit, GammaBicycle, AlfaWalk, AlfaBicycle, AlfaTransit, \
    AlfaCar, BetaBicycle, BetaTransit, BetaCar, BetaWalk, edges, PplVplOwnership

from polyline import decode, encode

vpl_query = {'vpl_acl': 'PMA'}
vpl_uides = [d['vpl_uide'] for d in vpl_old.find(vpl_query, {'vpl_uide': 1})]


def delete_all():
    print('Delete all. Are you sure?')
    sleep(5)
    execute_query('MATCH ()-[e]->() DELETE e')
    execute_query('MATCH (n) DELETE n')


def create_ppl_nodes():
    proj = {
        '_id': 0,
        'ppl_uide': 1,
        'vpl_uide': 1,
        'pplLngLat': 1,
        'ppl_owner': 1,
        'raw': '$ppl.raw',
        'wgh': '$ppl.wgh',
        'FTE': '$ppl_FTE',
        'vvm': '$vvm.vvm_1_std',
        'formattedAddress': '$goc.formattedAddress'
    }

    ppls = [d for d in ppl_old.find({'vpl_uide': {'$in': vpl_uides}}, proj)]
    n = [Node(
        type=NodeTypes.PPL,
        uide=d['ppl_uide'],
        lng=d['pplLngLat']['coordinates'][0],
        lat=d['pplLngLat']['coordinates'][1],
    ) for d in ppls]

    p = [PPL(
        uide=d['ppl_uide'],
        vpl_uide=d['vpl_uide'],
        lng=d['pplLngLat']['coordinates'][0],
        lat=d['pplLngLat']['coordinates'][1],
        owner=d['ppl_owner'],
        raw=d['raw'],
        wgh=d['wgh'],
        FTE=d['FTE'],
        vvm=d['vvm'],
        address=d['formattedAddress']
    ) for d in ppls]

    create_nodes_neo(nodes=n)
    create_nodes_mongo(nodes=p, collection=ppl)


def create_vpl_nodes():
    proj = {
        '_id': 0,
        'vpl_uide': 1,
        'vplLngLat': 1,
        'vpl_owner': 1,
        'vpl_name': 1
    }

    vpls = [VPL(
        uide=d['vpl_uide'],
        lng=d['vplLngLat']['coordinates'][0],
        lat=d['vplLngLat']['coordinates'][1],
        name=d['vpl_name']
    ) for d in vpl_old.find({'vpl_uide': {'$in': vpl_uides}}, proj)]

    create_nodes_neo(nodes=vpls)


def create_ppl_vpl_edges():
    proj = {
        '_id': 0,
        'ppl_uide': 1,
        'vpl_uide': 1
    }
    owners = [PplVplOwnership(uide_a=d['vpl_uide'],
                              uide_b=d['ppl_uide']) for d in ppl_old.find({'vpl_uide': {'$in': vpl_uides}}, proj)]

    create_edges(edges=owners)


def create_via_nodes():
    t: NodeTypes = NodeTypes.VIA
    proj = {
        '_id': 0,
        'via_uide': 1,
        'via_lng': 1,
        'via_lat': 1,
        'via_name': 1,
        'via_type': 1,
        'country': 1
    }

    vias = [VIA(
        uide=d['via_uide'],
        lng=d['via_lng'],
        lat=d['via_lat'],
        name=d['via_name'],
        via_type=d['via_type'],
        country=d['country'],
    ) for d in via_old.find({'isVisible': True}, proj)]

    create_nodes_neo(nodes=vias)


def create_gamma_edges():
    proj = {
        '_id': 0,
        'vpl_uide': 1,
        'ppl_uide': 1,
        'gamma': 1
    }

    gammas = list(gamma.find({'vpl_uide': {'$in': vpl_uides}}, proj))

    walks = [GammaWalk(
        uide_a=d['ppl_uide'],
        uide_b=d['vpl_uide'],
        polyline=d['gamma']['foot']['overview_polyline'],
        distance=d['gamma']['foot']['meter'],
        duration=d['gamma']['foot']['sec']
    ) for d in gammas if 'foot' in d['gamma'] and d['gamma']['foot']['meter']]

    cars = [GammaCar(
        uide_a=d['ppl_uide'],
        uide_b=d['vpl_uide'],
        polyline=d['gamma']['driv']['overview_polyline'],
        distance=d['gamma']['driv']['best_guess']['meter'],
        duration=d['gamma']['driv']['best_guess']['sec']
    ) for d in gammas if 'driv' in d['gamma'] and d['gamma']['driv']['best_guess']['meter']]

    transits = [GammaTransit(
        uide_a=d['ppl_uide'],
        uide_b=d['vpl_uide'],
        polyline=d['gamma']['publ']['overview_polyline'],
        distance=d['gamma']['publ']['meter'],
        duration=d['gamma']['publ']['sec']
    ) for d in gammas if 'publ' in d['gamma'] and d['gamma']['publ']['meter']]

    bicycles = [GammaBicycle(
        uide_a=d['ppl_uide'],
        uide_b=d['vpl_uide'],
        polyline=d['gamma']['bike']['overview_polyline'],
        distance=d['gamma']['bike']['meter'],
        duration=d['gamma']['bike']['sec']
    ) for d in gammas if 'bike' in d['gamma'] and d['gamma']['bike']['meter']]

    create_edges(edges=walks)
    create_edges(edges=cars)
    create_edges(edges=transits)
    create_edges(edges=bicycles)


def create_alfa_edges():
    proj = {
        '_id': 0,
        'ppl_uide': 1,
        'via_uide': 1,
        'alfaBikeMeter': 1,
        'alfaBikeSec': 1,
        'alfaDrivMeter': 1,
        'alfaDrivSec': 1,
        'alfaFootMeter': 1,
        'alfaFootSec': 1,
        'alfaPublMeter': 1,
        'alfaPublSec': 1,
        'ppl_lat': 1,
        'ppl_lng': 1,
        'via_lat': 1,
        'via_lng': 1
    }

    alfas = list(alfa.find({'ppl_LngLat': {'$exists': 1}, 'via_LngLat': {'$exists': 1}}, proj))

    def polyline(d: dict):
        return encode([(d['ppl_lat'], d['ppl_lng']), (d['via_lat'], d['via_lng'])])

    walks = [AlfaWalk(
        uide_a=d['ppl_uide'],
        uide_b=d['via_uide'],
        polyline=polyline(d),
        distance=d['alfaFootMeter'],
        duration=d['alfaFootSec']
    ) for d in alfas if d.get('alfaFootMeter') and d.get('alfaFootSec')]

    cars = [AlfaCar(
        uide_a=d['ppl_uide'],
        uide_b=d['via_uide'],
        polyline=polyline(d),
        distance=d['alfaDrivMeter'],
        duration=d['alfaDrivSec']
    ) for d in alfas if d.get('alfaDrivMeter') and d.get('alfaDrivSec')]

    transits = [AlfaTransit(
        uide_a=d['ppl_uide'],
        uide_b=d['via_uide'],
        polyline=polyline(d),
        distance=d['alfaPublMeter'],
        duration=d['alfaPublSec']
    ) for d in alfas if d.get('alfaPublMeter') and d.get('alfaPublSec')]

    bicycles = [AlfaBicycle(
        uide_a=d['ppl_uide'],
        uide_b=d['via_uide'],
        polyline=polyline(d),
        distance=d['alfaBikeMeter'],
        duration=d['alfaBikeSec']
    ) for d in alfas if d.get('alfaBikeMeter') and d.get('alfaBikeSec')]

    create_edges(edges=walks)
    create_edges(edges=cars)
    create_edges(edges=transits)
    create_edges(edges=bicycles)


def create_beta_edges():
    proj = {
        '_id': 0,
        'vpl_uide': 1,
        'via_uide': 1,
        'betaBikeMeter': 1,
        'betaBikeSec': 1,
        'betaDrivMeter': 1,
        'betaDrivSec': 1,
        'betaFootMeter': 1,
        'betaFootSec': 1,
        'betaPublMeter': 1,
        'betaPublSec': 1,
        'vpl_lat': 1,
        'vpl_lng': 1,
        'via_lat': 1,
        'via_lng': 1,
        'beta.routes.overview_polyline': 1
    }
    beta_query = {'vpl_LngLat': {'$exists': 1}, 'via_LngLat': {'$exists': 1}, 'vpl_uide': {'$in': vpl_uides}}
    betas = list(beta.find(beta_query, proj))

    def polyline(d: dict):
        return encode([(d['via_lat'], d['via_lng']), (d['vpl_lat'], d['vpl_lng'])])

    walks = [BetaWalk(
        uide_a=d['via_uide'],
        uide_b=d['vpl_uide'],
        polyline=polyline(d),
        distance=d['betaFootMeter'],
        duration=d['betaFootSec']
    ) for d in betas if d.get('betaFootMeter') and d.get('betaFootSec')]

    cars = [BetaCar(
        uide_a=d['via_uide'],
        uide_b=d['vpl_uide'],
        polyline=polyline(d),
        distance=d['betaDrivMeter'],
        duration=d['betaDrivSec']
    ) for d in betas if d.get('betaDrivMeter') and d.get('betaDrivSec')]

    transits = [BetaTransit(
        uide_a=d['via_uide'],
        uide_b=d['vpl_uide'],
        polyline=polyline(d) if 'beta' not in d else d['beta']['routes'][0]['overview_polyline']['points'][0],
        distance=d['betaPublMeter'],
        duration=d['betaPublSec']
    ) for d in betas if d.get('betaPublMeter') and d.get('betaPublSec')]

    bicycles = [BetaBicycle(
        uide_a=d['via_uide'],
        uide_b=d['vpl_uide'],
        polyline=polyline(d),
        distance=d['betaBikeMeter'],
        duration=d['betaBikeSec']
    ) for d in betas if d.get('betaBikeMeter') and d.get('betaBikeSec')]

    create_edges(edges=walks)
    create_edges(edges=cars)
    create_edges(edges=transits)
    create_edges(edges=bicycles)


# def create_gamma_car_route():
#     records: List[Record[Relationship]] = execute_query("MATCH (ppl:PPL)-[gammaCar:CAR]->(vpl:VPL) RETURN e")
#     features = []
#     for record in records:
#         rel: Relationship = record['gammaCar']
#         feature = Feature(geometry=LineString(decode(rel['polyline'], geojson=True)),
#                           properties={
#                               'duration': rel['duration'],
#                               'distance': rel['distance']
#                           })
#
#         features.append(feature)
#
#     print(geodumps(FeatureCollection(features)))


def create_node_indexes():
    for d in NodeTypes:
        qry = f"""
        CREATE CONSTRAINT {d}_uide_unique IF NOT EXISTS
        FOR (t:{d}) REQUIRE t.uide IS UNIQUE
        """
        execute_query(qry)


def create_edge_indexes():
    for d in edges:
        qry = f"""
        CREATE CONSTRAINT {d}_uide_unique IF NOT EXISTS
        FOR ()-[t:{d}]->() REQUIRE (t.uide_a, t.uide_b) IS UNIQUE
        """
        execute_query(qry)


def show_indexes():
    for d in execute_query("SHOW INDEXES"):
        if d['type'] == 'RANGE':
            print(d)


create_node_indexes()
create_edge_indexes()
show_indexes()

delete_all()
create_ppl_nodes()
create_vpl_nodes()
create_ppl_vpl_edges()
create_via_nodes()

create_gamma_edges()
create_alfa_edges()
create_beta_edges()

# create_gamma_car_route()
print('Done')
