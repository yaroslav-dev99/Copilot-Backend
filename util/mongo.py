from config import Config
from util.logger import Logger
from mongoengine import connection
from mongoengine import *
import time

def connect_mongo():
    Logger.i("connecting to mongodb...")
    
    try:
        connect(db = Config.MONGO_DB, host = Config.MONGO_URI)
    except ConnectionFailure:
        Logger.e("failed to connect mongodb. try again in 3s...")
        time.sleep(3)
        connect_mongo()
    
    Logger.i("connected to mongodb successfully.")

def disconnect_mongo():
    disconnect()

def get_next_sequence_val(sequence_name):
    sequence = connection.get_db()["counter"].find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        return_document = True,
        upsert = True
    )
    return sequence["sequence_value"]
