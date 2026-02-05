import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch
from core.detector import ScamDetectionResult

client = TestClient(app)

# Mock data
SCAM_MSG = "Urgent! Your bank account is locked. Click here: http://scam.com"
SAFE_MSG = "Hello, how are you?"

@pytest.fixture
def mock_dependencies():
    with patch("core.manager.ScamDetector.detect", new_callable=AsyncMock) as mock_detect, \
         patch("core.manager.HoneyPotAgent.generate_response", new_callable=AsyncMock) as mock_engage:
        
        yield mock_detect, mock_engage

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

def test_chat_scam_flow(mock_dependencies):
    mock_detect, mock_engage = mock_dependencies
    
    # Setup mocks
    mock_detect.return_value = ScamDetectionResult(
        is_scam=True, confidence=0.9, reason="Phishing link detected"
    )
    mock_engage.return_value = "Oh my! That sounds serious."
    
    # Request
    headers = {"X-API-Key": "test-key"} # We put check in main.py but in logic it accepts anything if env var not set
    payload = {"conversation_id": "test_scam_1", "message": SCAM_MSG}
    
    response = client.post("/chat", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["scam_detected"] is True
    assert data["response"] == "Oh my! That sounds serious."
    assert "http://scam.com" in data["metadata"]["intel"]["urls"]

def test_chat_safe_flow(mock_dependencies):
    mock_detect, mock_engage = mock_dependencies
    
    # Setup mocks
    mock_detect.return_value = ScamDetectionResult(
        is_scam=False, confidence=0.1, reason="Safe greeting"
    )
    
    # Request
    headers = {"X-API-Key": "test-key"}
    payload = {"conversation_id": "test_safe_1", "message": SAFE_MSG}
    
    response = client.post("/chat", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["scam_detected"] is False
    assert "who is this" in data["response"] # The default safe response

def test_extractor_logic():
    from core.extractor import IntelligenceExtractor
    extractor = IntelligenceExtractor()
    text = "Send money to my@upi and visit http://evil.com. Account: 1234567890"
    intel = extractor.extract(text)
    
    assert "my@upi" in intel.upi_ids
    assert "http://evil.com" in intel.urls
    assert "1234567890" in intel.bank_accounts
