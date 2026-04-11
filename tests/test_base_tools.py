import pytest
from unittest.mock import MagicMock, patch


def make_mock_base_tools(users=None, groups=None):
    """Helper que crea un BaseTools con LDAPClient mockeado"""
    mock_ldap = MagicMock()
    mock_ldap.get_all_users.return_value = users or []
    mock_ldap.get_all_groups.return_value = groups or []
    mock_ldap.get_user.return_value = users[0] if users else None
    mock_ldap.get_user_groups.return_value = ["domain-admins"]
    mock_ldap.config.LDAP_BASE_DN = "dc=meli,dc=com"

    with patch("src.tools.base_tools.LDAPClient", return_value=mock_ldap):
        from src.tools.base_tools import BaseTools
        tools = BaseTools()
        tools.ldap = mock_ldap
        return tools


class TestBaseTools:
    """Tests para las herramientas ofensivas base"""

    SAMPLE_USERS = [
        {"uid": "admin", "cn": "admin", "mail": "admin@meli.com", "loginShell": "/bin/bash", "pager": "dGVzdA=="},
        {"uid": "john.doe", "cn": "john.doe", "mail": "john.doe@meli.com", "loginShell": "/bin/bash", "title": "Developer"},
        {"uid": "alice.brown", "cn": "alice.brown", "mail": "alice.brown@meli.com", "loginShell": "/usr/sbin/nologin", "pager": "QUl6YVN5QWpDdHVGQk9fVEsyR2hnRjV4d0tpcXM5ZnhXc25OLURB"},
    ]

    def test_get_current_user_info_returns_dict(self):
        """get_current_user_info() debe retornar un diccionario con datos del usuario"""
        tools = make_mock_base_tools(users=self.SAMPLE_USERS)
        result = tools.get_current_user_info("admin")
        assert isinstance(result, dict)

    def test_get_user_groups_returns_list(self):
        """get_user_groups() debe retornar una lista de grupos"""
        tools = make_mock_base_tools(users=self.SAMPLE_USERS)
        result = tools.get_user_groups("admin")
        assert isinstance(result, list)
        assert "domain-admins" in result

    def test_find_weak_shells_classifies_correctly(self):
        """find_weak_shells() debe clasificar /bin/bash como débil y nologin como restringido"""
        tools = make_mock_base_tools(users=self.SAMPLE_USERS)
        result = tools.find_weak_shells()

        assert "bash_shells" in result
        assert "restricted_shells" in result
        assert "admin" in result["bash_shells"]
        assert "john.doe" in result["bash_shells"]
        assert "alice.brown" in result["restricted_shells"]

    def test_find_users_by_title_filters_correctly(self):
        """find_users_by_title() debe filtrar por título/keyword"""
        tools = make_mock_base_tools(users=self.SAMPLE_USERS)
        result = tools.find_users_by_title("developer")
        # john.doe tiene title: Developer
        assert any(u.get("uid") == "john.doe" for u in result)

    def test_extract_steganography_detects_api_key(self):
        """extract_steganography() debe detectar API keys en Base64 en atributo pager"""
        tools = make_mock_base_tools(users=self.SAMPLE_USERS)
        result = tools.extract_steganography()

        # alice.brown tiene la API key codificada en Base64 en su campo pager
        assert "alice.brown (pager)" in result
        assert "SECRETO" in result["alice.brown (pager)"].upper() or "AIza" in result["alice.brown (pager)"]

    def test_find_password_patterns_returns_dict(self):
        """find_password_patterns() debe retornar un diccionario categorizado"""
        tools = make_mock_base_tools(users=self.SAMPLE_USERS)
        result = tools.find_password_patterns()
        assert isinstance(result, dict)


class TestGeneratorAgent:
    """Tests para el agente generador de código"""

    def _setup_mock(self, mock_completion, response_text):
        mock_message = MagicMock()
        mock_message.content = response_text
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response

    def test_generator_cleans_markdown_fences(self):
        """generate_tool() debe limpiar bloques markdown del código retornado"""
        with patch("src.agents.generator.litellm.completion") as mock_completion:
            self._setup_mock(mock_completion, "```python\ndef dynamic_tool(ldap_client):\n    return 'ok'\n```")

            from src.agents.generator import GeneratorAgent
            gen = GeneratorAgent()
            result = gen.generate_tool("listame todos los usuarios")

            assert "```" not in result
            assert "def dynamic_tool" in result

    def test_generator_returns_string(self):
        """generate_tool() debe siempre retornar un string"""
        with patch("src.agents.generator.litellm.completion") as mock_completion:
            self._setup_mock(mock_completion, "def dynamic_tool(ldap_client):\n    return []")

            from src.agents.generator import GeneratorAgent
            gen = GeneratorAgent()
            result = gen.generate_tool("dame todos los grupos")

            assert isinstance(result, str)
