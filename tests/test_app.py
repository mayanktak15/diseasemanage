import json
from app.models import User, Consultation
from app.extensions import db


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_home_and_faq(client):
    r_home = client.get("/")
    assert r_home.status_code == 200
    assert b"Docify Online" in r_home.data

    r_faq = client.get("/faq")
    assert r_faq.status_code == 200
    assert b"Frequently Asked Questions" in r_faq.data


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard")
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers.get("Location", "")


def test_register_and_login_flow(client, app):
    # 1. Register User
    resp = client.post(
        "/register",
        data={
            "name": "Test Runner",
            "phone": "9990001234",
            "email": "runner@example.com",
            "password": "SecurePassword123"
        },
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Registration successful" in resp.data

    # Verify user in database
    with app.app_context():
        user = User.query.filter_by(email="runner@example.com").first()
        assert user is not None
        assert user.name == "Test Runner"

    # 2. Login User
    resp_login = client.post(
        "/login",
        data={
            "email": "runner@example.com",
            "password": "SecurePassword123"
        },
        follow_redirects=True
    )
    assert resp_login.status_code == 200
    assert b"Dashboard" in resp_login.data


def test_consultation_crud_and_soft_delete(client, app):
    # Register & Login first
    client.post(
        "/register",
        data={
            "name": "CRUD User",
            "phone": "1112223333",
            "email": "crud@example.com",
            "password": "Password123"
        },
        follow_redirects=True
    )
    client.post(
        "/login",
        data={"email": "crud@example.com", "password": "Password123"},
        follow_redirects=True
    )

    # 1. Create Consultation
    resp_create = client.post(
        "/dashboard",
        data={"symptoms": "Cough and mild headache"},
        follow_redirects=True
    )
    assert resp_create.status_code == 200
    assert b"Consultation form submitted successfully" in resp_create.data

    with app.app_context():
        user = User.query.filter_by(email="crud@example.com").first()
        consultations = Consultation.query.filter_by(user_id=user.id, is_deleted=False).all()
        assert len(consultations) == 1
        assert consultations[0].symptoms == "Cough and mild headache"
        cons_id = consultations[0].id

    # 2. Update Consultation
    resp_update = client.post(
        f"/update_consultation/{cons_id}",
        data={"symptoms": "Updated symptoms: sore throat"},
        follow_redirects=True
    )
    assert resp_update.status_code == 200
    assert b"Consultation updated successfully" in resp_update.data

    with app.app_context():
        cons = db.session.get(Consultation, cons_id)
        assert cons.symptoms == "Updated symptoms: sore throat"
        assert not cons.is_deleted

    # 3. Soft Delete Consultation
    resp_delete = client.post(f"/delete_consultation/{cons_id}")
    assert resp_delete.status_code == 200
    data = resp_delete.get_json()
    assert data["success"] is True

    # Verify that consultation is soft deleted in database
    with app.app_context():
        cons_deleted = db.session.get(Consultation, cons_id)
        assert cons_deleted.is_deleted is True

        # Ensure active query returns empty list
        active_consultations = Consultation.query.filter_by(user_id=user.id, is_deleted=False).all()
        assert len(active_consultations) == 0


def test_chatbot_endpoint(client):
    resp = client.post(
        "/chatbot",
        data=json.dumps({"message": "What is Docify?"}),
        content_type="application/json"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "reply" in data
    assert "Docify" in data["reply"]
