from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_refinement_add_personality():
    """User refines recommendation to add personality testing."""
    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Senior Java Developer"},
            {"role": "assistant", "content": "I recommend SHL Coding Simulations (Java) and SHL Verify Numerical Reasoning."},
            {"role": "user", "content": "Actually, please also include personality testing"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["end_of_conversation"], bool)

    # Response schema must remain strictly correct
    assert set(data.keys()) == {"reply", "recommendations", "end_of_conversation"}


def test_refinement_change_seniority():
    """User corrects seniority from senior to junior mid-conversation."""
    payload = {
        "messages": [
            {"role": "user", "content": "I need assessments for a Senior Python Developer"},
            {"role": "assistant", "content": "Here are recommendations for a Senior Python Developer..."},
            {"role": "user", "content": "Actually change that to Junior level"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"reply", "recommendations", "end_of_conversation"}


def test_refinement_change_role():
    """User corrects role mid-conversation."""
    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Data Scientist, Senior level"},
            {"role": "assistant", "content": "Here are recommendations for a Senior Data Scientist..."},
            {"role": "user", "content": "Actually I meant a Data Engineer, not Data Scientist"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"reply", "recommendations", "end_of_conversation"}
    assert isinstance(data["recommendations"], list)
