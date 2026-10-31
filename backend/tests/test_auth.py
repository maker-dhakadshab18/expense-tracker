from tests.conftest import register


def test_register_login_me(client):
    headers = register(client, "Alice@Example.com")
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"
    assert "password_hash" not in me.json()

    r = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_register_seeds_default_categories(client):
    headers = register(client)
    names = [c["name"] for c in client.get("/api/v1/categories", headers=headers).json()]
    assert "Food" in names and len(names) == 8


def test_duplicate_email_rejected(client):
    register(client)
    r = client.post("/api/v1/auth/register", json={"email": "A@example.com", "password": "password123"})
    assert r.status_code == 409


def test_wrong_password(client):
    register(client)
    r = client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_short_password_and_bad_email(client):
    assert client.post("/api/v1/auth/register", json={"email": "x@y.com", "password": "short"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={"email": "nope", "password": "password123"}).status_code == 422


def test_protected_routes_need_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/expenses").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
