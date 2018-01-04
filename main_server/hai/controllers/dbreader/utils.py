from io import StringIO
import configparser, os
from pymongo import MongoClient

def get_db():
    config = configparser.ConfigParser()

    ini_str = '[root]\n' + open('application.cfg', 'r').read()
    ini_fp = StringIO(ini_str)
    config.read_file(ini_fp)
    client = MongoClient('localhost', int(config["root"]["PORT_DB"]))
    return client.hai