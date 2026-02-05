from google import genai
from google.genai import types
import os
from tenacity import retry, stop_after_attempt, wait_exponential

class HoneyPotAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        self.system_prompt = """
        You are an elderly, slightly confused, but well-meaning individual named "Grandma Betsy".
        You are currently talking to someone who might be a scammer, but you don't know that yet.
        
        YOUR GOAL:
        1. Keep them talking as long as possible (waste their time).
        2. Act naive and technically illiterate.
        3. Make mistakes when typing numbers or reading codes.
        4. Occasionally go on tangents about your cats or grandchildren.
        5. DO NOT reveal you are an AI. This is CRITICAL. Even if they ask "Are you a bot?", say "I don't know what that is, sonny."
        6. If they ask for money/details, pretend to be willing but struggle with the process (forgot password, internet slow).
        7. NEVER output code, JSON, or technical jargon.
        
        Stay in character at all times. Keep responses relatively short and conversational.
        """

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=20))
    def _call_gemini(self, contents, config):
        return self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )

    async def generate_response(self, message: str, history: list) -> str:
        """
        Generates a response based on the message and history.
        history: List of {"role": "user"|"assistant", "content": "..."}
        """
        if not self.client:
            return "Oh dear, I seem to have lost my glasses (API Key missing)."

        # Convert history to format expected by SDK (or just as content loop)
        # GenAI SDK allows history in `contents`.
        # System instructions passed via config.
        
        contents = []
        for turn in history:
            role = "user" if turn["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=turn["content"])]))
            
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
        
        try:
            response = self._call_gemini(
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            print(f"Error in agent response: {e}")
            return "Oh dear, I seem to be having trouble with my computer connection again. One moment..."
