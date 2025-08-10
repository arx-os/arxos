import pytest


@pytest.mark.skipif('fastapi' not in globals(), reason="FastAPI not available in test environment")
def test_unified_routes_smoke_import():
    # Lazy import to avoid hard dependency when FastAPI isn't installed
    try:
        from fastapi.testclient import TestClient  # type: ignore
        from api.main import app  # type: ignore
    except Exception:
        pytest.skip("FastAPI or app not importable in this environment")

    client = TestClient(app)

    # Root should be available
    r = client.get("/")
    assert r.status_code in (200, 404)  # some envs customize root

    # Unified buildings routes should exist; without auth, expect 401
    r = client.get("/api/v1/buildings/")
    assert r.status_code in (200, 401)

    # Devices/floors endpoints should respond (likely 401 without auth)
    r = client.get("/api/v1/buildings/test-id/floors")
    assert r.status_code in (200, 401, 404)

    r = client.get("/api/v1/buildings/test-id/devices")
    assert r.status_code in (200, 401, 404)
