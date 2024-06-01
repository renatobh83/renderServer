import os
from pymongo import MongoClient

def mongoClient():
    try:
        return MongoClient(os.environ.get('URI'), connect=False, connectTimeoutMS=5000)
    except:
        return None
