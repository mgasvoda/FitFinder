import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# NOTE: This test is commented out because the project has been migrated from FastAPI to Chainlit
# The original FastAPI main.py file no longer exists
# from fastapi.testclient import TestClient
# from backend.main import app

# def test_root():
#     client = TestClient(app)
#     resp = client.get("/")
#     assert resp.status_code == 200
#     assert resp.json()["status"] == "FitFinder backend running"

# Placeholder test to keep the test file valid
def test_placeholder():
    """Placeholder test since the FastAPI app no longer exists"""
    assert True
