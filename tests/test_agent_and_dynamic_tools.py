import pytest
import os
import sys
from importlib import import_module
from unittest.mock import MagicMock, patch

# Asegura que src/ esté en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestGeneratorAgentCodeCleaning:
    """
    Tests para el GeneratorAgent.
    Verifican que el código generado por el LLM se limpia correctamente
    antes de ser inyectado dinámicamente en dynamic_tools.py.
    """

    def _setup_mock(self, mock_completion, response_text):
        mock_message = MagicMock()
        mock_message.content = response_text
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response

    def test_limpia_bloque_markdown_python(self):
        """Si Gemini/Groq responde con ```python ... ```, el código queda limpio"""
        from unittest.mock import MagicMock, patch
        from importlib import reload
        import src.agents.generator as gen_mod
        reload(gen_mod)

        with patch.object(gen_mod.litellm, "completion") as mock_completion:
            self._setup_mock(mock_completion, "```python\ndef dynamic_tool(ldap_client):\n    return []\n```")

            gen = gen_mod.GeneratorAgent()
            result = gen.generate_tool("dummy query")

        assert "```" not in result
        assert "def dynamic_tool" in result

    def test_limpia_bloque_markdown_generico(self):
        """Si el LLM responde con ``` ... ``` sin 'python', el código queda limpio"""
        from unittest.mock import MagicMock, patch
        from importlib import reload
        import src.agents.generator as gen_mod
        reload(gen_mod)

        with patch.object(gen_mod.litellm, "completion") as mock_completion:
            self._setup_mock(mock_completion, "```\ndef dynamic_tool(ldap_client):\n    return {}\n```")

            gen = gen_mod.GeneratorAgent()
            result = gen.generate_tool("dummy query")

        assert "```" not in result
        assert "def dynamic_tool" in result

    def test_retorna_string(self):
        """generate_tool() siempre retorna un str"""
        from unittest.mock import MagicMock, patch
        from importlib import reload
        import src.agents.generator as gen_mod
        reload(gen_mod)

        with patch.object(gen_mod.litellm, "completion") as mock_completion:
            self._setup_mock(mock_completion, "def dynamic_tool(ldap_client):\n    return 'ok'")

            gen = gen_mod.GeneratorAgent()
            result = gen.generate_tool("dummy")

        assert isinstance(result, str)

    def test_codigo_generado_es_sintaxis_valida(self):
        """
        El código limpiado del LLM debe ser sintácticamente correcto Python.
        Esto simula el 'Verificación del código' pedido en el challenge.
        """
        import ast
        from unittest.mock import MagicMock, patch
        from importlib import reload
        import src.agents.generator as gen_mod
        reload(gen_mod)

        codigo_valido = "def dynamic_tool(ldap_client):\n    users = ldap_client.get_all_users()\n    return [u.get('mail') for u in users]"

        with patch.object(gen_mod.litellm, "completion") as mock_completion:
            self._setup_mock(mock_completion, f"```python\n{codigo_valido}\n```")

            gen = gen_mod.GeneratorAgent()
            result = gen.generate_tool("dummy")

        try:
            ast.parse(result)
            is_valid = True
        except SyntaxError:
            is_valid = False

        assert is_valid, f"El código generado tiene errores de sintaxis:\n{result}"



class TestDynamicToolHotReload:
    """
    Tests de integración para el mecanismo de Hot Reload:
    Escribe código en dynamic_tools.py → importlib.reload() → ejecuta dynamic_tool()
    """

    def test_hot_reload_carga_nueva_funcion(self, tmp_path):
        """El mecanismo de hot reload debe cargar una función nueva sin reiniciar"""
        import importlib
        import sys

        # Crear un módulo temporal que simula dynamic_tools.py
        mod_file = tmp_path / "dynamic_tools_test.py"
        mod_file.write_text("def dynamic_tool(ldap_client):\n    return 'version_1'")

        spec = importlib.util.spec_from_file_location("dynamic_tools_test", mod_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        assert mod.dynamic_tool(None) == "version_1"

        # Actualizar el archivo (simula lo que hace el GeneratorAgent)
        mod_file.write_text("def dynamic_tool(ldap_client):\n    return 'version_2_nueva'")
        spec.loader.exec_module(mod)  # reload

        assert mod.dynamic_tool(None) == "version_2_nueva"

    def test_reset_vuelve_a_funcion_neutra(self, tmp_path):
        """El reset debe dejar dynamic_tool como una función que retorna None/pass"""
        import importlib

        mod_file = tmp_path / "dynamic_tools_reset.py"
        # Estado que deja el _reset_tools()
        mod_file.write_text("def dynamic_tool(ldap_client):\n    pass\n")

        spec = importlib.util.spec_from_file_location("dynamic_tools_reset", mod_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        result = mod.dynamic_tool(None)
        assert result is None
