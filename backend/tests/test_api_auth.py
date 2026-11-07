def test_login_success_and_me(client, admin_headers):
    resp = client.get("/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "test_admin"
    assert resp.json()["role"] == "administrator"


def test_login_invalid_password(client, admin_user):
    resp = client.post("/auth/login", data={"username": "test_admin", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post("/auth/login", data={"username": "ghost", "password": "whatever"})
    assert resp.status_code == 401


def test_protected_endpoint_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_only_admin_can_create_users(client, analyst_headers):
    resp = client.post("/auth/users", json={
        "username": "newbie", "email": "newbie@example.com", "password": "Newbie@123", "role": "security_analyst",
    }, headers=analyst_headers)
    assert resp.status_code == 403


def test_admin_can_create_user(client, admin_headers):
    resp = client.post("/auth/users", json={
        "username": "created_by_admin", "email": "created@example.com", "password": "Created@123",
        "role": "security_analyst",
    }, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["username"] == "created_by_admin"


def test_logout(client, admin_headers):
    resp = client.post("/auth/logout", headers=admin_headers)
    assert resp.status_code == 200
