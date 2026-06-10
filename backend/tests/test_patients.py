class TestPatients:
    def test_create_patient(self, client):
        resp = client.post(
            "/api/v1/patients/",
            json={"first_name": "Emma", "last_name": "Wilson", "phone": "5554445555"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["first_name"] == "Emma"
        assert "+1" in data["phone"]

    def test_duplicate_phone_rejected(self, client):
        client.post("/api/v1/patients/", json={"first_name": "A", "last_name": "B", "phone": "5556667777"})
        resp = client.post("/api/v1/patients/", json={"first_name": "C", "last_name": "D", "phone": "5556667777"})
        assert resp.status_code == 409

    def test_lookup_by_phone(self, client):
        client.post("/api/v1/patients/", json={"first_name": "Tom", "last_name": "Cruz", "phone": "5558889999"})
        resp = client.get("/api/v1/patients/lookup?phone=5558889999")
        assert resp.status_code == 200
        assert resp.json()["last_name"] == "Cruz"

    def test_lookup_nonexistent(self, client):
        resp = client.get("/api/v1/patients/lookup?phone=0000000000")
        assert resp.status_code == 404
