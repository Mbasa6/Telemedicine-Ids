"""Thin wrapper around the FastAPI backend for the Streamlit SOC dashboard."""
import requests

BACKEND_URL = "http://127.0.0.1:8000"


class ApiClient:
    def __init__(self, token: str | None = None):
        self.token = token

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def login(self, username, password):
        return requests.post(f"{BACKEND_URL}/auth/login", data={"username": username, "password": password})

    def get(self, path, params=None):
        return requests.get(f"{BACKEND_URL}{path}", headers=self._headers(), params=params)

    def post(self, path, json=None, files=None):
        return requests.post(f"{BACKEND_URL}{path}", headers=self._headers(), json=json, files=files)

    def put(self, path, json=None):
        return requests.put(f"{BACKEND_URL}{path}", headers=self._headers(), json=json)
