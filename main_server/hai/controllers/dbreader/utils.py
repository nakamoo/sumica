from io import StringIO
import configparser, os
from pymongo import MongoClient
from config import Config

def get_db():
    client = MongoClient('localhost', Config.PORT_DB)
    return client.hai