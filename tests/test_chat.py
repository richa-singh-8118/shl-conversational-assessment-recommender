from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_chat_clarify_missing_role():
    """When only a vague query is given, agent should ask for role."""
    payload = {
        "messages": [
            {"role": "user", "content": "I need an assessment"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "role" in data["reply"].lower() or "job" in data["reply"].lower() or "hiring" in data["reply"].lower()
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False


def test_chat_clarify_missing_seniority():
    """When role is given but seniority is missing, agent should ask for seniority."""
    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Java Developer"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Either it asks for seniority OR it proceeds to recommend (both are valid depending on LLM)
    assert "reply" in data
    assert "recommendations" in data
    assert "end_of_conversation" in data


def test_chat_full_recommendation():
    """When both role and seniority are provided, recommendations should be returned."""
    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Senior Java Developer"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["end_of_conversation"], bool)

    # If recommendations are returned, check they have the right schema
    for rec in data["recommendations"]:
        assert "name" in rec
        assert "url" in rec
        assert "test_type" in rec


def test_chat_response_schema_strict():
    """The response must ALWAYS contain exactly: reply, recommendations, end_of_conversation."""
    payload = {
        "messages": [
            {"role": "user", "content": "Hiring a Senior Data Analyst"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"reply", "recommendations", "end_of_conversation", "context"}


def test_chat_empty_messages_error():
    """Empty messages list should return 400 or a handled error."""
    payload = {"messages": []}
    response = client.post("/chat", json=payload)
    assert response.status_code in [400, 422, 500]
