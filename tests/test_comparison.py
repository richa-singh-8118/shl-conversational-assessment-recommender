from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_comparison_opq_gsa():
    payload = {
        "messages": [
            {"role": "user", "content": "Can you compare OPQ32r and GSA?"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False
    assert "|" in data["reply"]  # Check that a markdown table was generated
    assert "OPQ" in data["reply"]
    assert "GSA" in data["reply"]
