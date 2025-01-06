from neo4j import GraphDatabase
from app.settings import settings


URI = settings.NEO4J
AUTH = tuple(settings.GRAPHAUTH.split('/'))


def verify():
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()


verify()


def execute_query(query, **args):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        records, _, _ = driver.execute_query(query, **args, database="neo4j")
        return records
