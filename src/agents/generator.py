import re
import os
import litellm
from src.config import Config

# Silenciar logs verbose de litellm
litellm.suppress_debug_info = True

class GeneratorAgent:
    """
    Agente Generador provider-agnostico.
    Usa litellm para soportar +100 proveedores de LLM sin cambiar el código.
    Solo se necesita cambiar LLM_MODEL en el .env para switchear entre:
      - gemini/gemini-2.0-flash   (Google)
      - groq/llama-3.3-70b-versatile (Groq - gratuito)
      - gpt-4o-mini               (OpenAI)
      - anthropic/claude-3-haiku  (Anthropic)
    """
    def __init__(self):
        self.model = Config.LLM_MODEL
        # Exponemos las API keys como env vars para que litellm las detecte
        os.environ["GEMINI_API_KEY"] = Config.GEMINI_API_KEY
        os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY

    def generate_tool(self, query: str) -> str:
        print(f"[!] Solicitando al LLM ({self.model}) que construya una herramienta para: '{query}'...")

        system_prompt = """
Eres un experto en seguridad ofensiva y en Active Directory/OpenLDAP.
Tu tarea es crear UNA SOLA función Python que consulte el servidor LDAP.

Reglas CRÍTICAS:
1. Solo código Python puro, sin explicaciones ni comentarios extras.
2. La función se llama: dynamic_tool
3. Recibe un único parámetro: ldap_client
4. Usa: ldap_client.search(base_dn, filtro_ldap, lista_de_atributos)
5. Retorna string, list o dict.

Atributos disponibles en USUARIOS (ou=users,{ldap_client.config.LDAP_BASE_DN}):
- uid, cn, sn, givenName, mail, telephoneNumber, title, loginShell, userPassword, pager

Atributos disponibles en GRUPOS (ou=groups,{ldap_client.config.LDAP_BASE_DN}):
- cn, member, description, gidNumber

Ejemplo de uso correcto:
def dynamic_tool(ldap_client):
    base = f"ou=groups,{ldap_client.config.LDAP_BASE_DN}"
    results = ldap_client.search(base, "(objectClass=groupOfNames)", ["cn", "member"])
    return [r.get("cn") for r in results if r.get("cn")]

IMPORTANTE: ldap_client.search() ya devuelve strings directos en cada atributo (NO listas).
Nunca uses r.get("cn")[0]. Usa directamente r.get("cn").
SUPER CRÍTICO: Asegúrate siempre de incluir en 'lista_de_atributos' TODO atributo que pretendas extraer luego con r.get(). Si tu diccionario final usa r.get("cn") y r.get("mail"), la lista en la búsqueda DEBE SER obligatoriamente ["cn", "mail"]. Si no omites las claves, el resultado será vacío.
"""
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.1,
            max_tokens=1024
        )

        code = response.choices[0].message.content.strip()

        # Limpieza robusta de bloques Markdown
        code = re.sub(r"^```(python)?\n?", "", code)
        code = re.sub(r"\n?```$", "", code)
        return code.strip()
