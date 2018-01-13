class Config(object):
    FEATURES_SERVER_URL = 'localhost:5002'
    LOG_LEVEL = "debug"

    ENCRYPTION = False
    HOME = "/home/sean/HAI"
    ENCRYPTED_IMG_DIR = HOME + "/main_server/sumica/datafiles/images/encrypted_images/"
    RAW_IMG_DIR = HOME + "/main_server/sumica/datafiles/images/raw_images/"

    PORT = 5000
    DB_PORT = 27017

    CONTEXT = ('/etc/letsencrypt/live/homeai.ml/cert.pem', '/etc/letsencrypt/live/homeai.ml/privkey.pem')

    FB_TOKEN = 'EAAF0dXCeCJwBAC6DIb0KgrR0ZBY0TcgqfzNC2YSO2K6LIJn6PGFWfU9EkHvOqLtOMLQmUEfyhOP7BwG02DTW1BRYNiI3qR1Wu8KIjKwz5DLdWeXqAZCy0vvj1TdXZB0XFQYk1LM1KCDup2bpqHrhrttrxW0jdWk7hFygjzzHR9GZBQN4KckU'
    FB_BOT_ID = '318910425200757'

    # TODO remove
    USER = "sean"

class Config2(object): #dummy
    FEATURES_SERVER_URL = 'localhost:5002'
    LOG_LEVEL = "debug"

    ENCRYPTION = False
    HOME = "/home/sean/HAI"
    ENCRYPTED_IMG_DIR = HOME + "/main_server/hai/images/encrypted_images/"
    RAW_IMG_DIR = HOME + "/home/nakamura/HAI/main_server/hai/images/raw_images/"

    DB_PORT = 20202

    FB_TOKEN = 'EAAF0dXCeCJwBAC6DIb0KgrR0ZBY0TcgqfzNC2YSO2K6LIJn6PGFWfU9EkHvOqLtOMLQmUEfyhOP7BwG02DTW1BRYNiI3qR1Wu8KIjKwz5DLdWeXqAZCy0vvj1TdXZB0XFQYk1LM1KCDup2bpqHrhrttrxW0jdWk7hFygjzzHR9GZBQN4KckU'
    FB_BOT_ID = '318910425200757'