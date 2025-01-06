from pymongo import MongoClient
from app.settings import settings

client: MongoClient = MongoClient(settings.MONGODB)

users = client.auth.users
roles = client.auth.roles

vpl_old = client.m_scan.vpl
ppl_old = client.m_scan.ppl
via_old = client.m_scan.via
vvm_old = client.m_scan.vvm
gamma = client.m_scan.tetra_1_gamma
delta = client.m_scan.tetra_4_delta
alfa = client.m_scan.tetra_2_alfa
beta = client.m_scan.tetra_3_beta
clr = client.m_scan.clr
ico = client.m_scan.ico

routeTypes = client.m_traject.routeTypes
routes = client.m_traject.routes
ppl = client.m_traject.ppl
vvm_formatted = client.m_traject.vvmFormatted
vvm_observed = client.m_traject.vvmObserved
icons = client.m_traject.icons
rekenregels = client.m_traject.rekenregels
languages = client.m_traject.languages
translation_fields = client.m_traject.translationFields
owners = client.m_traject.owners
