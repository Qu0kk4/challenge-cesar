from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from src.tools.base_tools import BaseTools
from src.agents.generator import GeneratorAgent
from src.agents.auditor import AuditorAgent
import importlib
import sys
import os
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("Coordinator")
class AgentState(TypedDict):
    query: str
    tool_name: Optional[str]
    tool_result: Optional[str]
    needs_generation: bool
    generated_code: Optional[str]
    final_response: str

class Coordinator:
    def __init__(self):
        self.tools = BaseTools()
        self.available_tools = {
            "quien_soy": lambda state: self.tools.get_current_user_info(),
            "buscar_usuario": lambda state: self.tools.get_current_user_info(
                self._extract_username(state["query"])
            ),
            "mis_grupos": lambda state: self.tools.get_user_groups(
                self._extract_username(state["query"])
            ),
            "password_patterns": lambda state: self.tools.find_password_patterns(),
            "buscar_por_titulo": lambda state: self.tools.find_users_by_title(
                self._extract_title_keyword(state["query"])
            ),
            "esteganografia": lambda state: self.tools.extract_steganography(),
            "shells_debiles": lambda state: self.tools.find_weak_shells(),
            "enumerar_system": lambda state: self.tools.enumerate_system_ou(),
            "sudoers": lambda state: self.tools.find_sudoers(),
            "ssh_keys": lambda state: self.tools.find_ssh_keys(),
            "auditar_usuario": lambda state: AuditorAgent(self.tools.ldap).audit_user(
                self._extract_username(state["query"])
            ),
            "reset": lambda state: self._reset_tools(),
        }
        self.generator = GeneratorAgent()
        self.dynamic_tool_path = os.path.join(os.path.dirname(__file__), "..", "tools", "dynamic_tools.py")
        self.graph = self._build_graph()
    
    def _extract_username(self, query: str) -> str:
        """Extrae el username mencionado en la query, o usa 'admin' por defecto"""
        # Buscar patrones como 'de john.doe', 'de usuario X', etc.
        match = re.search(r"de\s+([\w\.\-]+)", query, re.IGNORECASE)
        if match:
            return match.group(1)
        # Buscar UIDs conocidos directamente en la query
        known_users = ["john.doe", "jane.smith", "bob.wilson", "alice.brown", "test.user", "carlos.rodriguez"]
        for user in known_users:
            if user in query.lower():
                return user
        return "admin"

    def _extract_title_keyword(self, query: str) -> str:
        """Extrae la palabra clave de título/cargo de la query"""
        role_words = ["developer", "manager", "analyst", "admin", "engineer", "tester", "security"]
        for word in role_words:
            if word in query.lower():
                return word
        # Si no encuentra keyword conocida, devuelve la query completa
        return query

    def _analyze_query(self, state: AgentState) -> AgentState:
        query = state["query"].lower()
        logger.info(f"Analizando query: '{state['query']}'")
        
        if any(x in query for x in ["quien soy", "quién soy", "mi info"]):
            state["tool_name"] = "quien_soy"
        elif any(x in query for x in ["pasame", "info de", "datos de", "busca a", "muéstrame a", "mostrame a"]):
            state["tool_name"] = "buscar_usuario"
        elif any(x in query for x in ["mis grupos", "grupos tengo", "grupos de", "qué grupos", "que grupos"]):
            state["tool_name"] = "mis_grupos"
        elif any(x in query for x in ["password", "contraseña", "patron"]):
            state["tool_name"] = "password_patterns"
        elif any(x in query for x in ["titulo", "cargo", "developer", "manager", "engineer", "analyst"]):
            state["tool_name"] = "buscar_por_titulo"
        elif any(x in query for x in ["oculto", "secreto", "base64", "pager", "esteganografi"]):
            state["tool_name"] = "esteganografia"
        elif any(x in query for x in ["shell", "bash", "login"]):
            state["tool_name"] = "shells_debiles"
        elif any(x in query for x in ["system", "ou system", "sensible"]):
            state["tool_name"] = "enumerar_system"
        elif any(x in query for x in ["sudo", "sudoers", "privilegios root", "reglas sudo"]):
            state["tool_name"] = "sudoers"
        elif any(x in query for x in ["ssh", "claves ssh", "llaves publicas", "llaves ssh"]):
            state["tool_name"] = "ssh_keys"
        elif any(x in query for x in ["auditar", "compliance", "riesgo de", "seguridad de", "revisar a"]):
            state["tool_name"] = "auditar_usuario"
        elif any(x in query for x in ["reset", "reiniciar", "limpiar"]):
            state["tool_name"] = "reset"
        else:
            logger.info("No se encontró herramienta. Delegando al GeneratorAgent.")
            state["needs_generation"] = True
        
        if state.get("tool_name"):
            logger.info(f"Herramienta seleccionada: {state['tool_name']}")
        return state
    
    def _execute_tool(self, state: AgentState) -> AgentState:
        tool_name = state.get("tool_name")
        if tool_name and tool_name in self.available_tools:
            try:
                logger.info(f"Ejecutando herramienta: {tool_name}")
                result = self.available_tools[tool_name](state)
                state["tool_result"] = str(result)
                state["final_response"] = f"Resultado de {tool_name}:\n{result}"
                logger.info(f"Herramienta '{tool_name}' ejecutada exitosamente")
            except Exception as e:
                logger.error(f"Error ejecutando '{tool_name}': {e}")
                state["final_response"] = f"Error ejecutando {tool_name}: {e}"
        return state
    
    def _generate_code(self, state: AgentState) -> AgentState:
        query = state["query"]
        code = self.generator.generate_tool(query)
        state["generated_code"] = code
        
        # 1. Guardar el código generado en dynamic_tools.py
        try:
            with open(self.dynamic_tool_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            # 2. Cargar/Recargar dinámicamente el módulo
            module_name = "src.tools.dynamic_tools"
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.import_module(module_name)
            
            from src.tools.dynamic_tools import dynamic_tool
            
            # 3. Registrar como "dynamic_executed" y ejecutar
            self.available_tools["dynamic_executed"] = lambda state: dynamic_tool(self.tools.ldap)
            
            # 4. Ejecutar la función
            state["tool_name"] = "dynamic_executed"
            state["needs_generation"] = False
            print("[+] Código generado e inyectado con éxito. Ejecutando...")
            
            # Delega la ejecución pasando al estado normal o lo corre directo aquí
            result = self.available_tools["dynamic_executed"](state)
            state["tool_result"] = str(result)
            state["final_response"] = f"🌟 ¡Nueva herramienta forjada!\n💻 Código Generado:\n```python\n{code}\n```\n\n🎯 Resultado:\n{result}"
            
        except Exception as e:
            error_msg = str(e)
            # Limpiar el error 429 para que sea legible
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                clean = "⚠️  Límite de cuota de la API de Gemini alcanzado.\n"
                clean += "   El GeneratorAgent no puede crear herramientas nuevas en este momento.\n"
                clean += "   Solución: Usá una API Key de un proyecto con billing habilitado en https://aistudio.google.com"
                state["final_response"] = clean
            else:
                state["final_response"] = f"❌ Error al generar herramienta: {error_msg[:200]}"
            logger.error(f"Error en generación/ejecución dinámica: {error_msg[:300]}")
            
        return state
        
    def _reset_tools(self) -> str:
        with open(self.dynamic_tool_path, "w", encoding="utf-8") as f:
            f.write("# Herramientas generadas dinámicamente\n\ndef dynamic_tool(ldap_client):\n    pass\n")
        
        if "dynamic_executed" in self.available_tools:
            del self.available_tools["dynamic_executed"]
            
        return "El Agente ha regresado a su estado original. Archivo dynamic_tools.py purgado."
    
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("analyze", self._analyze_query)
        workflow.add_node("execute", self._execute_tool)
        workflow.add_node("generate", self._generate_code)
        
        workflow.set_entry_point("analyze")
        workflow.add_conditional_edges(
            "analyze",
            lambda x: "generate" if x.get("needs_generation") else "execute",
            {"generate": "generate", "execute": "execute"}
        )
        workflow.add_edge("execute", END)
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def run(self, query: str) -> str:
        initial_state = AgentState(
            query=query,
            tool_name=None,
            tool_result=None,
            needs_generation=False,
            generated_code=None,
            final_response=""
        )
        result = self.graph.invoke(initial_state)
        return result["final_response"]
