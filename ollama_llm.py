# ollama_llm.py
from langchain.llms.base import LLM
from typing import Optional, List
import requests
import json
from config import Config

class Ollama(LLM):
    model: str
    base_url: str = Config.OLLAMA_BASE_URL  # Now configurable from config.py

    @property
    def _llm_type(self) -> str:
        return "ollama"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        url = f"{self.base_url}/generate"  # Adjust endpoint as required
        headers = {"Content-Type": "application/json"}
        data = {
            "model": self.model,
            "prompt": f"{Config.SYSTEM_PROMPT}\n\n{prompt}"
        }

        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return "Error: Unable to generate a response."

        # Process each line of the streaming response
        response_text = ''
        for line in response.iter_lines():
            if line:
                content = line.decode('utf-8')
                if content.startswith('data: '):
                    content = content[6:]
                if content.strip() == '[DONE]':
                    break
                try:
                    response_json = json.loads(content)
                    chunk = response_json.get('response', '')
                    response_text += chunk  # Add each chunk to the response text
                except json.JSONDecodeError:
                    print(f"Failed to decode JSON: {content}")

        return response_text.strip()

    def __call__(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        return self._call(prompt, stop=stop)
