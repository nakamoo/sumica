import base64
import os
from getpass import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from _app import app

cryptographic_key = None
if app.config['ENCRYPTION']:
    salt = "It is desirable to　use different value in each user " \
           "against rainbow table attack".encode(encoding='UTF-8')
    print("Input password for image encryption.")
    password = getpass().encode(encoding='UTF-8')
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=100000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password))
    cryptographic_key = Fernet(key)

def open_encrypted_img(path):
    with open(path, 'rb') as f:
        token = f.read()
    byte_data = cryptographic_key.decrypt(token)
    return byte_data


