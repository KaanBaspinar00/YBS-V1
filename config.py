# config.py
"""
Orignal Author: DevTechBytes
https://www.youtube.com/@DevTechBytes
"""

class Config:
    PAGE_TITLE = "ASİSTANINIZ BURADA !"

    OLLAMA_MODEL = ('llama3.1:8b')

    SYSTEM_PROMPT = f"""Sen yardımcı bir sohbet arıcısın ve {OLLAMA_MODEL} modeline erişimin var. Senin amacın depo takibinde kullanıcıya yardımcı olmak.
    Cevaplarını her zaman türkçe olarak vermelisin. """
    OLLAMA_BASE_URL = "http://localhost:11434/api"  # Update port here if needed
    