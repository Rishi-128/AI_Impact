# Agentic Honey-Pot System

An autonomous AI agent designed to engage scammers, waste their time, and extract intelligence (Bank Accounts, UPIs, URLs).

## Features
- **Scam Detection**: Uses Google Gemini 2.5 Flash to analyze intent.
- **Autonomous Engagement**: "Grandma Betsy" persona keeps scammers talking.
- **Intelligence Extraction**: Regex-based extraction of financial identifiers.
- **Resilient**: Implements retry logic for API stability.

## Prerequisites
- Python 3.9+
- Google Gemini API Key

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file:
   ```env
   GOOGLE_API_KEY=your_gemini_key_here
   SERVICE_API_KEY=your_chosen_secret
   ```

## Usage

Start the server:
```bash
uvicorn main:app --reload
```

## API Endpoints

### POST `/chat`
**Headers:**
- `X-API-Key`: `your_chosen_secret`

**Ref Body:**
```json
{
  "conversation_id": "unique_session_id",
  "message": "I am calling about your refund"
}
```

**Response:**
```json
{
  "scam_detected": true,
  "response": "Refund? Oh my...",
  "metadata": {
      "intel": { ... },
      "engagement_metrics": { ... }
  }
}
```
