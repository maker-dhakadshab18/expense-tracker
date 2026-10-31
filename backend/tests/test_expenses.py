from tests.conftest import register


def _cat_id(client, headers, name="Food"):
    return next(c["id"] for c in client.get("/api/v1/categories", headers=headers).json() if c["name"] == name)


def _create(client, headers, **overrides):
    body = {"amount": "250.50", "expense_date": "2026-10-15", "category_id": _cat_id(client, headers), "note": "lunch"}
    body.update(overrides)
    return client.post("/api/v1/expenses", json=body, headers=headers)


def test_expense_crud(client):
    h = register(client)
    r = _create(client, h)
    assert r.status_code == 201, r.text
    exp = r.json()
    assert exp["amount"] == "250.50"
    assert exp["category"]["name"] == "Food"

    r = client.patch(f"/api/v1/expenses/{exp['id']}", json={"amount": "99.99", "note": None}, headers=h)
    assert r.status_code == 200
    assert r.json()["amount"] == "99.99" and r.json()["note"] is None

    assert client.get(f"/api/v1/expenses/{exp['id']}", headers=h).status_code == 200
    assert client.delete(f"/api/v1/expenses/{exp['id']}", headers=h).status_code == 204
    assert client.get(f"/api/v1/expenses/{exp['id']}", headers=h).status_code == 404


def test_validation(client):
    h = register(client)
    assert _create(client, h, amount="0").status_code == 422
    assert _create(client, h, amount="-5").status_code == 422
    assert _create(client, h, amount="1.234").status_code == 422
    assert _create(client, h, expense_date="2026-13-01").status_code == 422
    assert _create(client, h, note="x" * 256).status_code == 422
    exp = _create(client, h).json()
    assert client.patch(f"/api/v1/expenses/{exp['id']}", json={"amount": None}, headers=h).status_code == 422


def test_user_b_cannot_touch_user_a_data(client):
    a = register(client, "a@example.com")
    b = register(client, "b@example.com")
    exp = _create(client, a).json()

    assert client.get(f"/api/v1/expenses/{exp['id']}", headers=b).status_code == 404
    assert client.patch(f"/api/v1/expenses/{exp['id']}", json={"amount": "1"}, headers=b).status_code == 404
    assert client.delete(f"/api/v1/expenses/{exp['id']}", headers=b).status_code == 404
    assert client.get("/api/v1/expenses", headers=b).json()["total"] == 0

    # B can't file an expense under A's category, or move their own expense into it
    a_food = _cat_id(client, a)
    assert _create(client, b, category_id=a_food).status_code == 422
    b_exp = _create(client, b).json()
    r = client.patch(f"/api/v1/expenses/{b_exp['id']}", json={"category_id": a_food}, headers=b)
    assert r.status_code == 422

    # A's expense is untouched
    assert client.get(f"/api/v1/expenses/{exp['id']}", headers=a).json()["amount"] == "250.50"


def test_filters_and_pagination(client):
    h = register(client)
    transport = _cat_id(client, h, "Transport")
    for day in range(1, 6):
        _create(client, h, expense_date=f"2026-10-0{day}")
    _create(client, h, expense_date="2026-09-30", category_id=transport)

    page = client.get("/api/v1/expenses?page_size=2", headers=h).json()
    assert page["total"] == 6 and len(page["items"]) == 2
    assert page["items"][0]["expense_date"] == "2026-10-05"  # newest first

    r = client.get("/api/v1/expenses?from=2026-10-02&to=2026-10-04", headers=h).json()
    assert r["total"] == 3
    r = client.get(f"/api/v1/expenses?category_id={transport}", headers=h).json()
    assert r["total"] == 1
    assert client.get("/api/v1/expenses?from=2026-10-05&to=2026-10-01", headers=h).status_code == 422


def test_categories_create(client):
    h = register(client)
    r = client.post("/api/v1/categories", json={"name": "  Pets  "}, headers=h)
    assert r.status_code == 201 and r.json()["name"] == "Pets"
    assert client.post("/api/v1/categories", json={"name": "pets"}, headers=h).status_code == 409
    assert client.post("/api/v1/categories", json={"name": "   "}, headers=h).status_code == 422


def test_monthly_summary(client):
    h = register(client)
    transport = _cat_id(client, h, "Transport")
    _create(client, h, amount="100.10", expense_date="2026-10-01")
    _create(client, h, amount="0.20", expense_date="2026-10-31")
    _create(client, h, amount="50.00", expense_date="2026-10-15", category_id=transport)
    _create(client, h, amount="999.00", expense_date="2026-11-01")  # outside month

    s = client.get("/api/v1/summary?month=2026-10", headers=h).json()
    assert s["total"] == "150.30"  # Decimal, no float drift
    assert s["count"] == 3
    assert s["by_category"][0]["category_name"] == "Food"
    assert s["by_category"][0]["total"] == "100.30"
    assert client.get("/api/v1/summary?month=2026-13", headers=h).status_code == 422

    other = register(client, "b@example.com")
    assert client.get("/api/v1/summary?month=2026-10", headers=other).json()["total"] == "0.00"


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "db": "ok"}
