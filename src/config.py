import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")
    LDAP_HOST = os.getenv("LDAP_HOST", "localhost")
    LDAP_PORT = int(os.getenv("LDAP_PORT", 389))
    LDAP_ADMIN_DN = os.getenv("LDAP_ADMIN_DN", "cn=admin,dc=meli,dc=com")
    LDAP_ADMIN_PASSWORD = os.getenv("LDAP_ADMIN_PASSWORD", "itachi")
    LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=meli,dc=com")
    
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY no encontrada")
