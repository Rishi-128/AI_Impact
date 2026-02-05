from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import os
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class ScamDetectionResult(BaseModel):
    is_scam: bool = Field(description="Whether the message is a scam or not")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reason: str = Field(description="Brief reason for the classification")

class ScamDetector:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def _call_gemini(self, prompt):
        return self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ScamDetectionResult
            )
        )

    async def detect(self, message: str, history: str = "") -> ScamDetectionResult:
        """
        Analyzes the message to detect scam intent.
        """
        if not self.client:
             return ScamDetectionResult(is_scam=False, confidence=0.0, reason="API Key missing")

        prompt = f"""
        You are an expert scam detector. Analyze the following incoming message and conversation history (if any).
        Determine if the user is attempting a scam (phishing, social engineering, fraud, investment scam, tech support scam, etc.).
        
        CRITICAL RULES:
        1. AVOID FALSE POSITIVES. Simple greetings ("Hi", "Hello"), harmless questions ("What is the time?"), or wrong numbers are NOT scams. 
        2. Only mark as scam if there is clear malicious intent (asking for money, OTP, passwords, urgent threats, suspicious links).
        3. If unsure, lean towards False.
        
        Focus on:
        - Urgency or threats
        - Requests for sensitive info (OTP, passwords, bank details)
        - Too good to be true offers / Unsolicited refunds
        - Suspicious links
        - Impersonation of authority/banks/tech support
        
        History:
        {history}
        
        New Message:
        {message}
        """

        try:
            # Using retry-wrapped function
            response = self._call_gemini(prompt)
            
            # Parse response
            if response.parsed:
                return response.parsed
            
            # Fallback text parsing if parsed not available (though it should be with schema)
            data = json.loads(response.text)
            return ScamDetectionResult(**data)
            
        except Exception as e:
            print(f"Error in detection: {e}")
            return ScamDetectionResult(is_scam=False, confidence=0.0, reason=f"Error: {str(e)}")
