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


def _auth_headers() -> dict:
    exp = int((datetime.utcnow() + timedelta(minutes=5)).timestamp())
    token = _make_jwt({"sub": "tester", "permissions": ["buildings:read"], "exp": exp})
    return {"Authorization": f"Bearer {token}"}


client = TestClient(app)


def test_list_with_filters_and_pagination():
    headers = _auth_headers()
    r = client.get("/api/v1/buildings", headers=headers, params={
        "building_type": "commercial",
        "status": "active",
        "city": "New York",
        "page": 1,
        "page_size": 5,
        "sort_by": "name",
        "sort_order": "asc"
    })
    assert r.status_code in (200, 204)
