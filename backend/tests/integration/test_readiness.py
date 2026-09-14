def test_readiness_checks_database_and_reports_provider_without_sending_email(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ok",
        "email_provider": "memory",
    }


def test_liveness_remains_independent_and_minimal(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
