from pymongo import MongoClient
from app.settings import get_settings

settings = get_settings()
client = MongoClient(settings.MONGODB)

vpl = client.m_scan.vpl
ppl = client.m_scan.ppl
gamma = client.m_scan.tetra_1_gamma
via = client.m_scan.via
alfa = client.m_scan.tetra_2_alfa
beta = client.m_scan.tetra_3_beta
route_types = client.m_traject.routeTypes
routes = client.m_traject.routes
