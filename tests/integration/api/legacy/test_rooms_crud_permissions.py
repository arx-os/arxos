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
    perms = perms or ["rooms:read", "rooms:create"]
    exp = int((datetime.utcnow() + timedelta(minutes=5)).timestamp())
    token = _make_jwt({"sub": "tester", "permissions": perms, "exp": exp})
    return {"Authorization": f"Bearer {token}"}


client = TestClient(app)


def test_rooms_list_with_jwt_and_filters():
    r = client.get("/api/v1/rooms", headers=_auth_headers(perms=["rooms:read"]), params={
        "room_type": "office",
        "status": "active",
        "page": 1,
        "page_size": 5
    })
    assert r.status_code in (200, 204)
    if r.status_code == 200:
        body = r.json()
        assert "data" in body and "pagination" in body["data"]


def test_rooms_create_forbidden_without_write():
    payload = {
        "floor_id": "floor_1",
        "room_number": "101",
        "name": "Test Room",
        "room_type": "office",
        "status": "active"
    }
    r = client.post("/api/v1/rooms/", headers=_auth_headers(perms=["rooms:read"]), json=payload)
    assert r.status_code in (401, 403)


def test_rooms_create_with_write():
    payload = {
        "floor_id": "floor_1",
        "room_number": "102",
        "name": "Room 102",
        "room_type": "office",
        "status": "active"
    }
    r = client.post("/api/v1/rooms/", headers=_auth_headers(perms=["rooms:read", "rooms:create", "write"]), json=payload)
    assert r.status_code in (200, 201)
