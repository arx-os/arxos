import json
from datetime import datetime, timedelta
import base64
import hmac
import hashlib

from fastapi.testclient import TestClient

from api.main import app
from application.config import get_security_config


def _make_jwt(payload: dict) -> str:
    sec = get_security_config()
    header = {"alg": sec.algorithm, "typ": "JWT"}
    def b64(d: bytes) -> str:
        return base64.urlsafe_b64encode(d).decode('utf-8').rstrip('=')
    h = b64(json.dumps(header).encode('utf-8'))
    p = b64(json.dumps(payload).encode('utf-8'))
    signing_input = f"{h}.{p}".encode('utf-8')
    sig = hmac.new(sec.secret_key.encode('utf-8'), signing_input, hashlib.sha256).digest()
    s = b64(sig)
    return f"{h}.{p}.{s}"


def _auth_headers(perms=None) -> dict:
    perms = perms or ["buildings:read", "buildings:create"]
    exp = int((datetime.utcnow() + timedelta(minutes=5)).timestamp())
    token = _make_jwt({"sub": "tester", "permissions": perms, "exp": exp})
    return {"Authorization": f"Bearer {token}"}


client = TestClient(app)


def test_create_requires_auth():
    payload = {
        "name": "NoAuth Building",
        "building_type": "commercial",
        "status": "active",
        "address": {
            "street": "1 Test Way",
            "city": "Testville",
            "state": "TS",
            "postal_code": "00000",
            "country": "USA"
        }
    }
    r = client.post("/api/v1/buildings/", json=payload)
    assert r.status_code == 401


def test_create_validation_error_missing_address():
    headers = _auth_headers()
    payload = {
        "name": "Invalid Building",
        "building_type": "commercial",
        "status": "active"
        # address missing
    }
    r = client.post("/api/v1/buildings/", headers=headers, json=payload)
    assert r.status_code in (400, 422)
