from pymongo import MongoClient
from app.settings import get_settings

settings = get_settings()
client = MongoClient(settings.MONGODB)

vpl_old = client.m_scan.vpl
ppl_old = client.m_scan.ppl
via_old = client.m_scan.via
vvm_old = client.m_scan.vvm
gamma = client.m_scan.tetra_1_gamma
delta = client.m_scan.tetra_4_delta
alfa = client.m_scan.tetra_2_alfa
beta = client.m_scan.tetra_3_beta
clr = client.m_scan.clr

routeTypes = client.m_traject.routeTypes
routes = client.m_traject.routes
ppl = client.m_traject.ppl
vvm_formatted = client.m_traject.vvmFormatted
vvm_observed = client.m_traject.vvmObserved
