#!/usr/bin/env python3
"""
Endpoint test suite for the Docify Flask app.
Uses Flask's test client to verify core routes work end-to-end.
Run: python testsprite.py
"""
import json
import os
import time
import unittest
import importlib
from pathlib import Path
from datetime import datetime

# Import app and DB models from the application
from app import app, db, User, Consultation
app_module = importlib.import_module('app')


class AppEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        # Ensure 127.0.0.1 is allowed; default is already '127.0.0.1/32'
        app.config["SECRET_KEY"] = "test-secret-key"
        cls.client = app.test_client()
        with app.app_context():
            # Reset database to a clean state for tests
            try:
                db.drop_all()
            except Exception:
                pass
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            try:
                db.session.remove()
                db.drop_all()
            except Exception:
                pass

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")

    def test_home_and_faq(self):
        # Home
        r_home = self.client.get("/")
        self.assertEqual(r_home.status_code, 200)
        self.assertIn(b"Docify Online", r_home.data)
        # FAQ
        r_faq = self.client.get("/faq")
        self.assertEqual(r_faq.status_code, 200)
        self.assertIn(b"Frequently Asked Questions", r_faq.data)

    def test_dashboard_requires_login(self):
        # Use a fresh client with no session cookies
        fresh_client = app.test_client()
        r_dash = fresh_client.get("/dashboard", follow_redirects=False)
        self.assertIn(r_dash.status_code, (301, 302))
        # Redirect should go to login
        self.assertIn("/login", r_dash.headers.get("Location", ""))

    def test_chatbot_missing_message_returns_400(self):
        r = self.client.post(
            "/chatbot",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)
        data = r.get_json()
        self.assertIsInstance(data, dict)
        self.assertIn("reply", data)

    def test_logout_clears_session(self):
        email = f"logout_{int(time.time())}@example.com"
        password = "LogoutPass!123"
        # Register and login
        self.client.post(
            "/register",
            data={
                "name": "Logout User",
                "phone": "9998887777",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

        # Access dashboard should be 200 when logged in
        r1 = self.client.get("/dashboard")
        self.assertEqual(r1.status_code, 200)

        # Logout
        r2 = self.client.get("/logout", follow_redirects=False)
        self.assertIn(r2.status_code, (301, 302))

        # Now dashboard should redirect to login
        r3 = self.client.get("/dashboard", follow_redirects=False)
        self.assertIn(r3.status_code, (301, 302))
        self.assertIn("/login", r3.headers.get("Location", ""))

    def test_ip_whitelist_blocks_non_allowed(self):
        # Temporarily narrow allow list to exclude localhost
        prev = list(getattr(app_module, 'ALLOWED_IPS', []))
        try:
            setattr(app_module, 'ALLOWED_IPS', ["10.0.0.0/8"])
            bad_client = app.test_client()
            # Simulate a client IP not in allowed range
            r = bad_client.get("/dashboard", environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
            self.assertEqual(r.status_code, 403)
            # Health should still work due to endpoint exemption
            r_h = bad_client.get("/health", environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
            self.assertEqual(r_h.status_code, 200)
        finally:
            setattr(app_module, 'ALLOWED_IPS', prev)

    def test_users_csv_export_after_register(self):
        email = f"csv_{int(time.time())}@example.com"
        password = "CsvPass!123"
        # Register user
        self.client.post(
            "/register",
            data={
                "name": "CSV User",
                "phone": "5554443333",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        # Check users.csv exists and contains the email
        users_csv = Path("users.csv")
        self.assertTrue(users_csv.exists())
        content = users_csv.read_text(encoding="utf-8", errors="ignore")
        self.assertIn(email, content)

    def test_query_dataset_csv_append_on_chat(self):
        # Ensure logged in for symptom context
        email = f"qds_{int(time.time())}@example.com"
        password = "QdsPass!123"
        self.client.post(
            "/register",
            data={
                "name": "QDS User",
                "phone": "1231231234",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

        msg = f"hello-from-tests-{int(time.time())}"
        self.client.post(
            "/chatbot",
            data=json.dumps({"message": msg}),
            content_type="application/json",
        )
        qfile = Path("query_dataset.csv")
        self.assertTrue(qfile.exists())
        content = qfile.read_text(encoding="utf-8", errors="ignore")
        self.assertIn(msg, content)

    def test_profile_update_flow(self):
        email = f"profile_{int(time.time())}@example.com"
        password = "ProfPass!123"
        # Register and login
        self.client.post(
            "/register",
            data={
                "name": "Profile User",
                "phone": "1212121212",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

        # GET profile
        r_get = self.client.get("/profile")
        self.assertEqual(r_get.status_code, 200)

        # POST profile update
        r_post = self.client.post(
            "/profile",
            data={
                "name": "Profile User Updated",
                "phone": "9090909090",
                "age": "30",
                "gender": "Other",
                "blood_group": "O+",
                "medical_history": "None",
                "allergies": "Pollen",
            },
            follow_redirects=True,
        )
        self.assertEqual(r_post.status_code, 200)
        # Expect success flash message appears in response body
        self.assertIn(b"Profile updated successfully", r_post.data)

        # Verify in DB
        with app.app_context():
            u = User.query.filter_by(email=email).first()
            self.assertIsNotNone(u)
            self.assertEqual(u.name, "Profile User Updated")
            self.assertEqual(u.phone, "9090909090")
            self.assertEqual(u.age, 30)
            self.assertEqual(u.gender, "Other")
            self.assertEqual(u.blood_group, "O+")
            self.assertEqual(u.medical_history, "None")
            self.assertEqual(u.allergies, "Pollen")

    def test_delete_consultation_json(self):
        email = f"del_{int(time.time())}@example.com"
        password = "DelPass!123"
        # Register and login
        self.client.post(
            "/register",
            data={
                "name": "Del User",
                "phone": "7776665555",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

        # Create a consultation
        self.client.post(
            "/dashboard",
            data={"symptoms": "Temp entry to delete"},
            follow_redirects=True,
        )

        with app.app_context():
            u = User.query.filter_by(email=email).first()
            cons = Consultation.query.filter_by(user_id=u.id).order_by(Consultation.created_at.desc()).first()
            cons_id = cons.id

        # Delete via JSON route
        r = self.client.post(f"/delete_consultation/{cons_id}")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("success"))

        # Verify deletion
        with app.app_context():
            exists = Consultation.query.get(cons_id)
            self.assertIsNone(exists)

    def test_update_status_json(self):
        # Unauthenticated should get 401 (use a fresh client with no session)
        fresh_client = app.test_client()
        r_unauth = fresh_client.post("/update_status/1", json={"status": "reviewed"})
        self.assertEqual(r_unauth.status_code, 401)

        # Create user and consultation
        email = f"status_{int(time.time())}@example.com"
        password = "StatPass!123"
        self.client.post(
            "/register",
            data={
                "name": "Status User",
                "phone": "1010101010",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )
        self.client.post(
            "/dashboard",
            data={"symptoms": "Needs review"},
            follow_redirects=True,
        )

        with app.app_context():
            u = User.query.filter_by(email=email).first()
            cons = Consultation.query.filter_by(user_id=u.id).order_by(Consultation.created_at.desc()).first()
            cons_id = cons.id
            prev_updated = cons.updated_at

        # Update status
        r = self.client.post(
            f"/update_status/{cons_id}",
            json={"status": "reviewed", "doctor_notes": "Checked"},
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("success"))

        # Verify DB updated
        with app.app_context():
            cons2 = Consultation.query.get(cons_id)
            self.assertEqual(cons2.status, "reviewed")
            self.assertEqual(cons2.doctor_notes, "Checked")
            self.assertGreaterEqual(cons2.updated_at, prev_updated)

    def test_update_consultation_timestamps(self):
        email = f"time_{int(time.time())}@example.com"
        password = "TimePass!123"
        # Register/login
        self.client.post(
            "/register",
            data={
                "name": "Time User",
                "phone": "2323232323",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )
        self.client.post(
            "/dashboard",
            data={"symptoms": "Initial"},
            follow_redirects=True,
        )

        with app.app_context():
            u = User.query.filter_by(email=email).first()
            cons = Consultation.query.filter_by(user_id=u.id).order_by(Consultation.created_at.desc()).first()
            cons_id = cons.id
            created_at_before = cons.created_at
            updated_at_before = cons.updated_at

        # Update consultation
        r_up_post = self.client.post(
            f"/update_consultation/{cons_id}",
            data={"symptoms": "Updated symptoms"},
            follow_redirects=True,
        )
        self.assertEqual(r_up_post.status_code, 200)
        self.assertIn(b"Consultation updated successfully", r_up_post.data)

        with app.app_context():
            cons2 = Consultation.query.get(cons_id)
            self.assertEqual(cons2.symptoms, "Updated symptoms")
            self.assertEqual(cons2.created_at, created_at_before)
            self.assertGreaterEqual(cons2.updated_at, updated_at_before)

    def test_404_error_page(self):
        r = self.client.get("/this-route-does-not-exist")
        self.assertEqual(r.status_code, 404)

    def test_register_login_dashboard_and_consultation_flow(self):
        # Unique email for this test run
        email = f"user_{int(time.time())}@example.com"
        password = "TestPassword!123"

        # 1. Register
        r_reg = self.client.post(
            "/register",
            data={
                "name": "Test User",
                "phone": "1234567890",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        self.assertEqual(r_reg.status_code, 200)
        self.assertIn(b"Registration successful", r_reg.data)

        # 2. Login
        r_login = self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )
        self.assertEqual(r_login.status_code, 200)
        self.assertIn(b"Dashboard", r_login.data)

        # 3. Submit Consultation
        r_submit = self.client.post(
            "/dashboard",
            data={"symptoms": "Headache and mild fever"},
            follow_redirects=True,
        )
        self.assertEqual(r_submit.status_code, 200)
        self.assertIn(b"Consultation form submitted successfully", r_submit.data)

        # 4. Confirm consultation visible
        r_dash = self.client.get("/dashboard")
        self.assertEqual(r_dash.status_code, 200)
        self.assertIn(b"Headache and mild fever", r_dash.data)

        # 5. Extract the consultation ID to test update
        with app.app_context():
            u = User.query.filter_by(email=email).first()
            self.assertIsNotNone(u)
            if not u:
                self.fail("User not created")
                return
            cons = Consultation.query.filter_by(user_id=u.id).order_by(Consultation.created_at.desc()).first()
            self.assertIsNotNone(cons)
            if not cons:
                self.fail("Consultation not created")
                return
            cons_id = cons.id

        # 6. GET update page
        r_up_get = self.client.get(f"/update_consultation/{cons_id}")
        self.assertEqual(r_up_get.status_code, 200)
        self.assertIn(b"Update Consultation", r_up_get.data)

        # 7. POST update
        r_up_post = self.client.post(
            f"/update_consultation/{cons_id}",
            data={"symptoms": "Updated symptoms: cough and fatigue"},
            follow_redirects=True,
        )
        self.assertEqual(r_up_post.status_code, 200)
        self.assertIn(b"Consultation updated successfully", r_up_post.data)
        self.assertIn(b"Updated symptoms: cough and fatigue", r_up_post.data)

    def test_chatbot_endpoint(self):
        # Ensure logged in user for symptom context (optional)
        email = f"bot_{int(time.time())}@example.com"
        password = "BotPass!123"
        self.client.post(
            "/register",
            data={
                "name": "Bot User",
                "phone": "1112223333",
                "email": email,
                "password": password,
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )
        # Add a consultation so chatbot can pick latest symptoms
        self.client.post(
            "/dashboard",
            data={"symptoms": "Fever for 2 days"},
            follow_redirects=True,
        )

        # Call chatbot
        payload = {"message": "hello"}
        r_bot = self.client.post(
            "/chatbot",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(r_bot.status_code, 200)
        data = r_bot.get_json()
        self.assertIsInstance(data, dict)
        self.assertIn("reply", data)
        self.assertTrue(isinstance(data["reply"], str))
        self.assertGreater(len(data["reply"]), 0)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AppEndpointTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    # Exit with non-zero on failure for CI friendliness
    raise SystemExit(0 if result.wasSuccessful() else 1)
