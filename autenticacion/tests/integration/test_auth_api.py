import pytest


class TestAuthApi:
    def _register(self, client, email="user@example.com", password="Str0ngPass", actor_type=None):
        payload = {"email": email, "password": password}
        if actor_type is not None:
            payload["actor_type"] = actor_type
        return client.post("/auth/register", json=payload)

    def _login(self, client, email="user@example.com", password="Str0ngPass"):
        return client.post("/auth/login", json={"email": email, "password": password})

    # --- /auth/register -------------------------------------------------

    def test_register_returns_201_and_the_user_payload(self, client):
        response = self._register(client)

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "user@example.com"
        assert "id" in body

    def test_register_defaults_to_non_admin_human_actor(self, client):
        response = self._register(client)

        body = response.json()
        assert body["is_admin"] is False
        assert body["actor_type"] == "human"

    def test_register_accepts_agent_actor_type(self, client):
        response = self._register(client, actor_type="agent")

        assert response.status_code == 201
        assert response.json()["actor_type"] == "agent"

    def test_register_rejects_an_unknown_actor_type(self, client):
        response = self._register(client, actor_type="robot")

        assert response.status_code == 422

    def test_register_duplicate_email_returns_409(self, client):
        self._register(client)

        response = self._register(client)

        assert response.status_code == 409

    def test_register_invalid_email_returns_422_from_schema_validation(self, client):
        # EmailStr rejects malformed emails at the schema boundary, before the
        # domain's Email value object would ever get a chance to run.
        response = self._register(client, email="not-an-email")

        assert response.status_code == 422

    def test_register_password_without_digit_returns_400(self, client):
        response = self._register(client, password="alllettersnodigit")

        assert response.status_code == 400

    def test_register_password_below_minimum_length_returns_422(self, client):
        response = self._register(client, password="a1a1a1a")  # 7 chars

        assert response.status_code == 422

    def test_register_password_at_minimum_length_boundary_succeeds(self, client):
        response = self._register(client, password="a1a1a1a1")  # exactly 8 chars

        assert response.status_code == 201

    # --- /auth/login ------------------------------------------------------

    def test_login_with_valid_credentials_returns_a_token_pair(self, client):
        self._register(client)

        response = self._login(client)

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["expires_in"] == pytest.approx(3600, abs=5)

    def test_login_with_wrong_password_returns_401(self, client):
        self._register(client)

        response = self._login(client, password="WrongPass1")

        assert response.status_code == 401

    def test_login_with_unknown_email_returns_401(self, client):
        response = self._login(client, email="ghost@example.com")

        assert response.status_code == 401

    # --- /auth/validate -----------------------------------------------

    def test_validate_a_freshly_issued_access_token_is_valid(self, client):
        self._register(client)
        access_token = self._login(client).json()["access_token"]

        response = client.post("/auth/validate", json={"token": access_token})

        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_validate_exposes_admin_aud_and_permissions_claims(self, client):
        self._register(client, actor_type="agent")
        access_token = self._login(client).json()["access_token"]

        response = client.post("/auth/validate", json={"token": access_token})

        body = response.json()
        assert body["is_admin"] is False
        assert body["aud"] == "agent"
        assert body["permissions"] == ["user"]

    def test_validate_a_garbage_token_is_reported_invalid_with_200(self, client):
        response = client.post("/auth/validate", json={"token": "garbage.token.value"})

        assert response.status_code == 200
        assert response.json()["valid"] is False

    def test_validate_a_refresh_token_as_access_token_is_invalid(self, client):
        self._register(client)
        refresh_token = self._login(client).json()["refresh_token"]

        response = client.post("/auth/validate", json={"token": refresh_token})

        assert response.status_code == 200
        assert response.json()["valid"] is False

    # --- /auth/refresh ----------------------------------------------------

    def test_refresh_returns_a_new_token_pair(self, client):
        self._register(client)
        login_body = self._login(client).json()

        response = client.post("/auth/refresh", json={"refresh_token": login_body["refresh_token"]})

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] != login_body["access_token"]
        assert body["refresh_token"] != login_body["refresh_token"]

    def test_reusing_a_rotated_refresh_token_returns_401(self, client):
        self._register(client)
        refresh_token = self._login(client).json()["refresh_token"]
        client.post("/auth/refresh", json={"refresh_token": refresh_token})

        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 401

    def test_refresh_with_an_access_token_is_rejected(self, client):
        self._register(client)
        access_token = self._login(client).json()["access_token"]

        response = client.post("/auth/refresh", json={"refresh_token": access_token})

        assert response.status_code == 401

    def test_refresh_with_a_garbage_token_returns_401(self, client):
        response = client.post("/auth/refresh", json={"refresh_token": "garbage"})

        assert response.status_code == 401
