import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_me_csrf_and_logout(client: AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "OWNER@EXAMPLE.COM", "password": "a secure integration password"},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "OWNER"
    set_cookie = ";".join(login.headers.get_list("set-cookie")).lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "owner@example.com"

    missing_csrf = await client.post("/api/v1/auth/logout")
    assert missing_csrf.status_code == 403

    csrf = client.cookies["motorscope_csrf"]
    logout = await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert logout.status_code == 200
    assert logout.json() == {"success": True}
    assert (await client.get("/api/v1/auth/me")).status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_login_is_uniform_and_rate_limited(client: AsyncClient) -> None:
    payload = {"email": "missing@example.com", "password": "a wrong password value"}
    first = await client.post("/api/v1/auth/login", json=payload)
    second = await client.post("/api/v1/auth/login", json=payload)
    third = await client.post("/api/v1/auth/login", json=payload)
    assert first.status_code == second.status_code == 401
    assert first.json()["detail"] == second.json()["detail"]
    assert third.status_code == 429
    assert third.headers["retry-after"] == "60"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_checks_real_dependencies(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
