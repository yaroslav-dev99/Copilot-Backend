from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from entity.member import Member
from util.logger import Logger
from config import Config
import requests
import base64
import json
import jwt

def get_member_by_ms_id(ms_id: str) -> Member:
    response = requests.get(
        Config.MS_BASE_URL + "/members/" + ms_id,
        headers = { "x-api-key": Config.MS_XAPI_KEY } 
    )
    if response.status_code == 200:
        obj = response.json()
        return Member(obj.get("data", {}))
    else:
        Logger.e(f"get_member_by_id failed: {ms_id}")
        return None

def get_ms_id_by_token(ms_token: str) -> str:
    public_key = get_public_key()
    ms_id = None
    
    try:
        decoded = jwt.decode(
            ms_token,
            public_key,
            algorithms = "RS256",
            audience = Config.MS_AUDIENCE,
            options = { "verify_signature": True }
        )
        ms_id = decoded.get("id")
    except jwt.InvalidTokenError as e:
        Logger.e(f"get_ms_id_by_token failed: {ms_token} {e}")

    return ms_id

def base64url_decode(input):
    input += "=" * (4 - (len(input) % 4))
    return base64.urlsafe_b64decode(input.encode("utf-8"))

def get_public_key():
    response = requests.get(Config.MS_PUB_KEY_URL)
    key_data = json.loads(response.text)
    key_info = key_data["keys"][0]

    n = int.from_bytes(base64url_decode(key_info["n"]), "big")
    e = int.from_bytes(base64url_decode(key_info["e"]), "big")

    public_numbers = RSAPublicNumbers(e, n)
    public_key = public_numbers.public_key(backend = default_backend())

    pem_data = public_key.public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_str = pem_data.decode("utf-8")    
    return public_key_str
