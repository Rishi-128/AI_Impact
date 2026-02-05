from .detector import ScamDetector
from .agent import HoneyPotAgent
from .extractor import IntelligenceExtractor, ExtractedIntelligence
from typing import Dict, Any, List
import time
from pydantic import BaseModel

class EngagementMetrics(BaseModel):
    start_time: float
    duration_seconds: float = 0.0
    turn_count: int = 0

class HoneyPotManager:
    def __init__(self):
        self.detector = ScamDetector()
        self.agent = HoneyPotAgent()
        self.extractor = IntelligenceExtractor()
        # In-memory storage: {conversation_id: {"history": [], "scam_detected": False, "intel": {}}}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    async def process_message(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """
        Orchestrates the honey-pot logic.
        """
        # 1. Initialize session if new
        if conversation_id not in self.sessions:
            self.sessions[conversation_id] = {
                "history": [],
                "scam_detected": False,
                "intel": ExtractedIntelligence().dict(),
                "metrics": EngagementMetrics(start_time=time.time()).dict()
            }
        
        session = self.sessions[conversation_id]
        metrics = session["metrics"]
        
        # Update metrics
        metrics["turn_count"] += 1
        metrics["duration_seconds"] = time.time() - metrics["start_time"]
        
        # 2. Extract Intelligence immediately (from their message)
        new_intel = self.extractor.extract(message)
        self._merge_intel(session["intel"], new_intel)
        
        # 3. Detect Scam (if not already detected)
        if not session["scam_detected"]:
            # Format history for detector
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in session["history"]])
            detection_result = await self.detector.detect(message, history_str)
            
            # Store latest detection details
            session["detection_details"] = {
                "confidence": detection_result.confidence,
                "reason": detection_result.reason
            }
            
            if detection_result.is_scam:
                session["scam_detected"] = True
                print(f"Scam Detected in {conversation_id}: {detection_result.reason}")

        # 4. Generate Response
        response_text = ""
        metadata = {
            "scam_detected": session["scam_detected"],
            "detection_details": session.get("detection_details", {}),
            "intel": session["intel"],
            "engagement_metrics": metrics
        }

        if session["scam_detected"]:
            # Auto-engage
            response_text = await self.agent.generate_response(message, session["history"])
        else:
            # Not a scam (yet) - Echo or simple acknowledgement
            # In a real scenario, we might just stay silent or act as a passive user
            # For this problem statement: "Accept incoming scam messages... engage scammers autonomously after detection"
            # If not detected, maybe we just say "Hello?" or wait. 
            # Let's be a generic user if not sure.
            response_text = "I'm sorry, who is this?"

        # 5. Update History
        session["history"].append({"role": "user", "content": message})
        session["history"].append({"role": "assistant", "content": response_text})
        
        return {
            "scam_detected": session["scam_detected"],
            "response": response_text,
            "metadata": metadata
        }

    def _merge_intel(self, current: Dict, new: ExtractedIntelligence):
        """Helper to merge new intelligence into existing session storage."""
        for field in ["bank_accounts", "upi_ids", "urls", "phone_numbers"]:
            # pydantic models return list, we append unique
            existing = set(current.get(field, []))
            incoming = getattr(new, field)
            existing.update(incoming)
            current[field] = list(existing)
