import re
from pydantic import BaseModel
from typing import List, Optional

class ExtractedIntelligence(BaseModel):
    bank_accounts: List[str] = []
    upi_ids: List[str] = []
    urls: List[str] = []
    phone_numbers: List[str] = []

class IntelligenceExtractor:
    def extract(self, text: str) -> ExtractedIntelligence:
        """
        Extracts structured intelligence using Regex.
        """
        intel = ExtractedIntelligence()
        
        # 1. UPI IDs (e.g., name@okicici, numbers@ybl)
        upi_pattern = r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}'
        intel.upi_ids = list(set(re.findall(upi_pattern, text)))
        
        # 2. URLs (http/https)
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*'
        intel.urls = list(set(re.findall(url_pattern, text)))
        
        # 3. Bank Account Numbers (Simple heuristic: 9-18 digits, avoiding phone numbers)
        # This is tricky without context, but we look for sequences.
        # Phone numbers often start with + or 0, account numbers often don't in chat.
        # We'll use a broad digit matcher and you might refine it.
        # Let's look for "Account" or "Acc" context or just long digits.
        # For now, simplistic: 9 to 18 digits.
        digit_sequences = re.findall(r'\b\d{9,18}\b', text)
        intel.bank_accounts = list(set(digit_sequences)) # This will catch phones too potentially
        
        # 4. Phone Numbers (10 digits, maybe +91)
        phone_pattern = r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        # This is very broad. Let's stick to common Indian/US formats if needed.
        # Strict 10 digit:
        mobile_pattern = r'\b[6-9]\d{9}\b'
        intel.phone_numbers = list(set(re.findall(mobile_pattern, text)))
        
        # Filter bank accounts that are also phone numbers
        intel.bank_accounts = [acc for acc in intel.bank_accounts if acc not in intel.phone_numbers]
        
        return intel
