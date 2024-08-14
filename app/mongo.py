from pymongo import MongoClient
from app.settings import get_settings

settings = get_settings()
client = MongoClient(settings.MONGODB)

vpl_old = client.m_scan.vpl
ppl_old = client.m_scan.ppl
via_old = client.m_scan.via
gamma = client.m_scan.tetra_1_gamma
alfa = client.m_scan.tetra_2_alfa
beta = client.m_scan.tetra_3_beta

routeTypes = client.m_traject.routeTypes
routes = client.m_traject.routes
ppl = client.m_traject.ppl
