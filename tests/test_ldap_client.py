import pytest
from unittest.mock import MagicMock, patch


class TestLDAPClient:
    """Tests para el cliente LDAP"""

    def test_connect_success(self):
        """Verifica que connect() retorna True cuando LDAP responde OK"""
        with patch("ldap.initialize") as mock_ldap:
            mock_conn = MagicMock()
            mock_ldap.return_value = mock_conn

            from src.ldap_client import LDAPClient
            client = LDAPClient()
            result = client.connect()

            assert result is True
            mock_conn.simple_bind_s.assert_called_once()

    def test_connect_failure(self):
        """Verifica que connect() retorna False cuando falla la conexión"""
        with patch("ldap.initialize") as mock_ldap:
            import ldap as ldap_module
            mock_ldap.return_value.simple_bind_s.side_effect = ldap_module.LDAPError("Connection refused")

            from src.ldap_client import LDAPClient
            client = LDAPClient()
            result = client.connect()

            assert result is False

    def test_search_returns_list(self):
        """Verifica que search() devuelve una lista de resultados"""
        with patch("ldap.initialize") as mock_ldap:
            mock_conn = MagicMock()
            mock_ldap.return_value = mock_conn
            mock_conn.search_s.return_value = [
                ("cn=john,ou=users,dc=meli,dc=com", {
                    "cn": [b"john"],
                    "mail": [b"john@meli.com"]
                })
            ]

            from src.ldap_client import LDAPClient
            client = LDAPClient()
            client.connect()
            results = client.search("ou=users,dc=meli,dc=com", "(objectClass=*)")

            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0]["cn"] == "john"
            assert results[0]["mail"] == "john@meli.com"

    def test_search_returns_empty_on_error(self):
        """Verifica que search() retorna lista vacía en caso de error"""
        with patch("ldap.initialize") as mock_ldap:
            import ldap as ldap_module
            mock_conn = MagicMock()
            mock_ldap.return_value = mock_conn
            mock_conn.simple_bind_s.return_value = None
            mock_conn.search_s.side_effect = ldap_module.LDAPError("Search failed")

            from src.ldap_client import LDAPClient
            client = LDAPClient()
            client.connect()
            results = client.search("ou=users,dc=meli,dc=com", "(objectClass=*)")

            assert results == []
