import unittest
import json

from app import app, db, MERCH_ITEMS

class APITestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def get_token(self, username="testuser", password="testpass"):
        response = self.app.post("/api/auth", json={"username": username, "password": password})
        data = json.loads(response.data)
        return data.get("token")

    def test_auth_and_info(self):
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        response = self.app.get("/api/info", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["coins"], 1000)
        self.assertEqual(data["inventory"], [])
        self.assertEqual(data["coinHistory"]["received"], [])
        self.assertEqual(data["coinHistory"]["sent"], [])

    def test_send_coin(self):
        token1 = self.get_token(username="user1", password="pass1")
        token2 = self.get_token(username="user2", password="pass2")
        headers1 = {"Authorization": f"Bearer {token1}"}

        response = self.app.post("/api/sendCoin", json={"toUser": "user2", "amount": 100}, headers=headers1)
        self.assertEqual(response.status_code, 200)

        response1 = self.app.get("/api/info", headers=headers1)
        data1 = json.loads(response1.data)
        self.assertEqual(data1["coins"], 900)

        headers2 = {"Authorization": f"Bearer {token2}"}
        response2 = self.app.get("/api/info", headers=headers2)
        data2 = json.loads(response2.data)
        self.assertEqual(data2["coins"], 1100)
        self.assertEqual(len(data2["coinHistory"]["received"]), 1)
        self.assertEqual(data2["coinHistory"]["received"][0]["fromUser"], "user1")

    def test_buy_item(self):
        token = self.get_token(username="buyer", password="pass")
        headers = {"Authorization": f"Bearer {token}"}
        item = "cup"
        response = self.app.get(f"/api/buy/{item}", headers=headers)
        self.assertEqual(response.status_code, 200)

        response_info = self.app.get("/api/info", headers=headers)
        data_info = json.loads(response_info.data)
        self.assertEqual(data_info["coins"], 1000 - MERCH_ITEMS[item])

        self.assertEqual(len(data_info["inventory"]), 1)
        self.assertEqual(data_info["inventory"][0]["type"], item)
        self.assertEqual(data_info["inventory"][0]["quantity"], 1)

    def test_buy_nonexistent_item(self):
        token = self.get_token(username="buyer2", password="pass")
        headers = {"Authorization": f"Bearer {token}"}
        response = self.app.get("/api/buy/nonexistent", headers=headers)
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
