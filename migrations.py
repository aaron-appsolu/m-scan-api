import json
from datetime import datetime
from time import sleep, time
from typing import Dict, List
import requests

from pymongo import UpdateOne

from app.neo import execute_query
from app.mongo import vpl_old, ppl_old, vvm_old, vvm_observed, vvm_formatted, gamma, delta, via_old, alfa, beta, ppl, \
    clr, ico, icons
from app.structure.nodes import PPL, VPL, VIA, MEETINGPOINT, NodeTypes, Node
from app.structure.graph_types import create_edges, create_nodes_neo, create_nodes_mongo
from app.structure.edges import PplVplOwnership, Gamma, Beta, Alfa, DeltaStart, DeltaOverlap, DeltaEnd, Edge

from polyline import encode
from app.structure.types import VVMObserved, VVMFormatted, Modals
from helpers import checksum, md5, chunks

vpl_query = {'vpl_acl': 'PMA'}
vpl_uides = [d['vpl_uide'] for d in vpl_old.find(vpl_query, {'vpl_uide': 1})]

CURRENTLY_SMART = [
    "[Home office]",
    "Te voet",
    "Fiets",
    "Fiets of Te voet",
    "eBike",
    "E-bike",
    "E-Fiets",
    "E-fiets",
    "Pedelec",
    "E-step",
    "SpeedPedelec",
    "Speed-Pedelec",
    "Speed Pedelec",
    "Speed pedelec",
    "Bromfiets",
    "Scooter",
    "E-Scooter",
    "Moto",
    "E-Moto",
    "Bus",
    "Tram",
    "Tram / Bus",
    "Trein",
    "Openbaar Vervoer",
    "OV plus",
    "OV-keten",
    "P+R",
    "W+R",
    "B+R",
    "Bike+Ride",
    "D+R",
    "Collectief Vervoer",
    "Meerijden / Oppikken",
    "Laatste kilometers delen",
    "Carpool",
    "DeWaterbus",
    "iBus",
    "Fietsbus",
    "Laatste kilometers delen",
    "Carpool thuis",
    "Carpool gedeeld traject",
    "CarpoolParking",
    "via Carpool Parking",
]


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
        'vvm': {'std': '$vvm.vvm_1_std', 'rpt': '$vvm.vvm_1_rpt', 'obs': '$vvm.vvm_1_obs'},
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
        vvm_uide=checksum(d['vvm']['obs']),
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


def create_vvm():
    res = list(vvm_old.find({'vvm_owner': vpl_query['vpl_acl']}, {
        'obs': '$vvm_obs',
        'rpt': '$vvm_rpt',
        'std': '$vvm_std',
        'bw': '$vvm_bw',
        'uide': '$vvm_uide',
        'traject': '$vvm_traject',
    }))
    translate_traject: Dict[str, Modals] = {
        'Fiets': Modals.BICYCLE,
        'Auto': Modals.CAR,
        'Openbaar Vervoer': Modals.TRANSIT
    }
    vvms_obs = [VVMObserved(
        uide=d['uide'],
        value=d['obs'],
        std_uide=md5(d['std']),
        rpt_uide=md5(d['rpt'])
    ) for d in res]

    vvms_std = [VVMFormatted(
        uide=md5(d['std']),
        value=d['std'],
        type='std',
        icon_uide=None,
        is_bedrijfswagen=d['bw'] == 1,
        is_smart=d['std'] in CURRENTLY_SMART,
        traject=translate_traject.get(d['traject']),
    ) for d in res]

    vvms_rpt = [VVMFormatted(
        uide=md5(d['rpt'] + 'reported'),
        value=d['rpt'],
        type='rpt',
        icon_uide=None,
        is_bedrijfswagen=d['bw'] == 1,
        is_smart=d['rpt'] in CURRENTLY_SMART,
        traject=translate_traject.get(d['traject']),
    ) for d in res]

    timestamp = datetime.now()
    operations_1 = [UpdateOne({'uide': d.uide, 'type': d.type}, {
        '$setOnInsert': {'created': timestamp},
        '$set': {**d.model_dump(), 'lastEdited': timestamp}
    }, upsert=True) for d in vvms_obs]

    operations_2 = [UpdateOne({'uide': d.uide, 'type': d.type}, {
        '$setOnInsert': {'created': timestamp},
        '$set': {**d.model_dump(), 'lastEdited': timestamp}
    }, upsert=True) for d in vvms_std + vvms_rpt]

    vvm_observed.bulk_write(operations_1)
    vvm_formatted.bulk_write(operations_2)


def create_gamma_edges():
    proj = {
        '_id': 0,
        'vpl_uide': 1,
        'ppl_uide': 1,
        'gamma': 1
    }

    gammas = list(gamma.find({'vpl_uide': {'$in': vpl_uides}}, proj))

    walks = [Gamma(
        uide_a=d['ppl_uide'],
        uide_b=d['vpl_uide'],
        type=Modals.WALK,
        polyline=d['gamma']['foot']['overview_polyline'],
        distance=d['gamma']['foot']['meter'],
        duration=d['gamma']['foot']['sec']
    ) for d in gammas if 'foot' in d['gamma'] and d['gamma']['foot']['meter']]

    cars = [Gamma(
        uide_a=d['ppl_uide'],
        uide_b=d['vpl_uide'],
        type=Modals.CAR,
        polyline=d['gamma']['driv']['overview_polyline'],
        distance=d['gamma']['driv']['best_guess']['meter'],
        duration=d['gamma']['driv']['best_guess']['sec']
    ) for d in gammas if 'driv' in d['gamma'] and d['gamma']['driv']['best_guess']['meter']]

    transits = [Gamma(
        uide_a=d['ppl_uide'],
        uide_b=d['vpl_uide'],
        type=Modals.TRANSIT,
        polyline=d['gamma']['publ']['overview_polyline'],
        distance=d['gamma']['publ']['meter'],
        duration=d['gamma']['publ']['sec']
    ) for d in gammas if 'publ' in d['gamma'] and d['gamma']['publ']['meter']]

    bicycles = [Gamma(
        uide_a=d['ppl_uide'],
        uide_b=d['vpl_uide'],
        type=Modals.BICYCLE,
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

    walks = [Alfa(
        uide_a=d['ppl_uide'],
        uide_b=d['via_uide'],
        type=Modals.WALK,
        polyline=polyline(d),
        distance=d['alfaFootMeter'],
        duration=d['alfaFootSec']
    ) for d in alfas if d.get('alfaFootMeter') and d.get('alfaFootSec')]

    cars = [Alfa(
        uide_a=d['ppl_uide'],
        uide_b=d['via_uide'],
        type=Modals.CAR,
        polyline=polyline(d),
        distance=d['alfaDrivMeter'],
        duration=d['alfaDrivSec']
    ) for d in alfas if d.get('alfaDrivMeter') and d.get('alfaDrivSec')]

    transits = [Alfa(
        uide_a=d['ppl_uide'],
        uide_b=d['via_uide'],
        type=Modals.TRANSIT,
        polyline=polyline(d),
        distance=d['alfaPublMeter'],
        duration=d['alfaPublSec']
    ) for d in alfas if d.get('alfaPublMeter') and d.get('alfaPublSec')]

    bicycles = [Alfa(
        uide_a=d['ppl_uide'],
        uide_b=d['via_uide'],
        type=Modals.BICYCLE,
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

    walks = [Beta(
        uide_a=d['via_uide'],
        uide_b=d['vpl_uide'],
        type=Modals.WALK,
        polyline=polyline(d),
        distance=d['betaFootMeter'],
        duration=d['betaFootSec']
    ) for d in betas if d.get('betaFootMeter') and d.get('betaFootSec')]

    cars = [Beta(
        uide_a=d['via_uide'],
        uide_b=d['vpl_uide'],
        type=Modals.CAR,
        polyline=polyline(d),
        distance=d['betaDrivMeter'],
        duration=d['betaDrivSec']
    ) for d in betas if d.get('betaDrivMeter') and d.get('betaDrivSec')]

    transits = [Beta(
        uide_a=d['via_uide'],
        uide_b=d['vpl_uide'],
        type=Modals.TRANSIT,
        polyline=polyline(d) if 'beta' not in d else d['beta']['routes'][0]['overview_polyline']['points'][0],
        distance=d['betaPublMeter'],
        duration=d['betaPublSec']
    ) for d in betas if d.get('betaPublMeter') and d.get('betaPublSec')]

    bicycles = [Beta(
        uide_a=d['via_uide'],
        uide_b=d['vpl_uide'],
        type=Modals.BICYCLE,
        polyline=polyline(d),
        distance=d['betaBikeMeter'],
        duration=d['betaBikeSec']
    ) for d in betas if d.get('betaBikeMeter') and d.get('betaBikeSec')]

    create_edges(edges=walks)
    create_edges(edges=cars)
    create_edges(edges=transits)
    create_edges(edges=bicycles)


def create_delta():
    query = [
        {'$match': {'vpl_uide': {'$in': vpl_uides}, 'delta': {'$ne': '[VOID]'}}},
        {'$unwind': {'path': '$delta'}},
        {'$project': {
            'ppl_uide_1': '$ppl_uide',
            'ppl_uide_2': '$delta.pplTo',
            'vpl_uide': '$vpl_uide',
            'poly1': '$delta.poly1',
            'poly2': '$delta.poly2',
        }},
        # {'$skip': 796584}, => indexError, pol2 is only 1 coords long
        # {'$limit': 1}
    ]

    meeting_points: List[MEETINGPOINT] = []
    start_segment: List[Edge] = []
    overlap_segment: List[Edge] = []
    end_segment: List[Edge] = []

    deltas = list(delta.aggregate(query))
    l_deltas = len(deltas)
    for idx, d in enumerate(deltas):
        url = f"http://localhost:8000/overlap?encoded_1={d['poly1']}&encoded_2={d['poly2']}"
        res = requests.get(url)
        if res.status_code != 200:
            continue
        j = res.json()
        ppl_uide_1 = d['ppl_uide_1']
        ppl_uide_2 = d['ppl_uide_2']
        vpl_uide = d['vpl_uide']
        lng_a, lat_a = j['first_closest']
        lng_b, lat_b = j['last_closest']
        m_a_uide = md5(f"{lng_a}_{lat_a}")
        m_b_uide = md5(f"{lng_b}_{lat_b}")

        meeting_points.append(MEETINGPOINT(
            uide=m_a_uide,
            lng=lng_a,
            lat=lat_a
        ))

        meeting_points.append(MEETINGPOINT(
            uide=m_b_uide,
            lng=lng_b,
            lat=lat_b
        ))

        start_segment.append(DeltaStart(
            uide_a=ppl_uide_1,
            uide_b=m_a_uide,
            type=Modals.CAR,
            polyline=j['start_polyline_1'],
            distance=j['start_1'],
            duration=j['start_1'] * 16.666  # 60 kmh => 16.666 m/s
        ))

        start_segment.append(DeltaStart(
            uide_a=ppl_uide_2,
            uide_b=m_a_uide,
            type=Modals.CAR,
            polyline=j['start_polyline_2'],
            distance=j['start_2'],
            duration=j['start_2'] * 16.666  # 60 kmh => 16.666 m/s
        ))

        overlap_segment.append(DeltaOverlap(
            uide_a=m_a_uide,
            uide_b=m_b_uide,
            type=Modals.CAR,
            polyline=j['overlap_polyline_1'],
            distance=j['overlap_1'],
            duration=j['overlap_1'] * 16.666  # 60 kmh => 16.666 m/s
        ))

        end_segment.append(DeltaEnd(
            uide_a=m_b_uide,
            uide_b=vpl_uide,
            type=Modals.CAR,
            polyline=j['end_polyline_1'],
            distance=j['end_1'],
            duration=j['end_1'] * 16.666  # 60 kmh => 16.666 m/s
        ))

        # overlap_segment.append(DeltaOverlap(
        #     uide_a=m_a_uide,
        #     uide_b=m_b_uide,
        #     type=Modals.CAR,
        #     polyline=res['overlap_polyline_2'],
        #     distance=res['overlap_2'],
        #     duration=res['overlap_2'] * 16.666  # 60 kmh => 16.666 m/s
        # ))
        #
        # end_segment.append(DeltaEnd(
        #     uide_a=m_b_uide,
        #     uide_b=vpl_uide,
        #     type=Modals.CAR,
        #     polyline=res['end_polyline_2'],
        #     distance=res['end_2'],
        #     duration=res['end_2'] * 16.666  # 60 kmh => 16.666 m/s
        # ))
        print(f"Calculated: {idx + 1}/{l_deltas}")

    create_nodes_neo(nodes=meeting_points)
    create_edges(edges=start_segment)
    create_edges(edges=overlap_segment)
    create_edges(edges=end_segment)


def create_node_indexes():
    for d in NodeTypes:
        qry = f"""
        CREATE CONSTRAINT {d}_uide_unique IF NOT EXISTS
        FOR (t:{d}) REQUIRE t.uide IS UNIQUE
        """
        execute_query(qry)


def create_edge_indexes():
    for d in Modals:
        qry = f"""
        CREATE CONSTRAINT {d}_uide_unique IF NOT EXISTS
        FOR ()-[t:{d}]->() REQUIRE (t.uide_a, t.uide_b) IS UNIQUE
        """
        execute_query(qry)


def show_indexes():
    for d in execute_query("SHOW INDEXES"):
        if d['type'] == 'RANGE':
            print(d)


def fix_clr():
    vvm_formatted.update_many({}, {'$set': {'colour.potential': '#000000', 'colour.nu': '#000000'}})
    colour_translations = {
        'blue': '#0000ff',
        'cyan': '#00ffff',
        'red': '#ff0000',
        'gray59': '#595959'
    }
    for idx, clrs in enumerate(clr.find({vpl_query['vpl_acl']: {'$exists': 1}})):
        colour = clrs[vpl_query['vpl_acl']]
        clr_uide = clrs['clr_uide']
        key = 'potential' if clrs['potential'] == 1 else 'nu'
        vvm_formatted.update_many({'uide': clr_uide},
                                  {'$set': {f'colour.{key}': colour_translations.get(colour, colour)}})
        print(idx)


def create_icons():
    icos = ico.find({'PMA': {'$exists': 1, '$ne': None}},
                    {'url': {'$concat': ['https://m-scan.made4it.com/_icons/', '$PMA']},
                     'path': '$PMA',
                     'ico_name': 1,
                     'potential': 1,
                     'uide': '$ico_uide'})

    for idx, d in enumerate(icos):
        svg = requests.get(d['url']).text
        name = d['ico_name'].replace('/', '_').replace(' ', '')
        path = f"assets/icons/{name}_{'nu' if d['potential'] == 0 else 'potential'}.svg"
        with open(f"./{path}", 'w') as file:
            file.write(svg)

        icons.update_one({'uide': d['uide']}, {'$set': {
            'uide': d['uide'],
            'name': d['ico_name'],
            'path.nu' if d['potential'] == 0 else 'path.potential': path
        }}, upsert=True)
        print(idx)


# create_node_indexes()
# create_edge_indexes()
# show_indexes()

# delete_all()
# create_ppl_nodes()
# create_vpl_nodes()
# create_ppl_vpl_edges()
# create_via_nodes()
# create_vvm()

# create_gamma_edges()
# create_alfa_edges()
# create_beta_edges()
# create_delta()
# fix_clr()
create_icons()

print('Done')
