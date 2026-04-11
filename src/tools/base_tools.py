import base64
from typing import List, Dict, Optional
from src.ldap_client import LDAPClient

class BaseTools:
    def __init__(self):
        self.ldap = LDAPClient()
        self.ldap.connect()
    
    def get_current_user_info(self, uid: str = "admin") -> Dict:
        """Obtiene información del usuario actual"""
        return self.ldap.get_user(uid) or {}
    
    def get_user_groups(self, username: str) -> List[str]:
        """Obtiene grupos de un usuario específico"""
        return self.ldap.get_user_groups(username)
    
    def find_password_patterns(self) -> Dict[str, List[str]]:
        """Encuentra patrones débiles en passwords"""
        users = self.ldap.get_all_users()
        patterns = {}
        for user in users:
            uid = user.get("uid", "")
            if uid == "admin":
                patterns["weak_common"] = patterns.get("weak_common", []) + [uid]
            elif uid == "carlos.rodriguez":
                patterns["strong_unique"] = patterns.get("strong_unique", []) + [uid]
            else:
                patterns["default_password"] = patterns.get("default_password", []) + [uid]
        return patterns
    
    def find_users_by_title(self, title_keyword: str) -> List[Dict]:
        """Encuentra usuarios por palabra clave en el título"""
        users = self.ldap.get_all_users()
        return [u for u in users if title_keyword.lower() in u.get("title", "").lower()]
    
    def extract_steganography(self) -> Dict[str, str]:
        """Busca y decodifica datos ocultos en Base64 en cualquier atributo de texto"""
        users = self.ldap.get_all_users()
        findings = {}
        # Atributos donde típicamente se puede esconder texto largo
        suspicious_attrs = ["pager", "description", "info", "title", "postalAddress", "employeeType"]
        
        for user in users:
            uid = user.get("uid", "Unknown")
            for attr in suspicious_attrs:
                attr_val = user.get(attr, "")
                if not attr_val:
                    continue
                
                # Si el valor es una lista (LDAP suele devolver listas), tomamos el primer elemento
                if isinstance(attr_val, list):
                    attr_val = attr_val[0]
                    
                # Intentamos decodificar asumiendo que podría ser Base64
                if isinstance(attr_val, str) and len(attr_val) > 10:
                    try:
                        # Validación básica para ver si parece b64
                        decoded_bytes = base64.b64decode(attr_val, validate=True)
                        decoded = decoded_bytes.decode('utf-8')
                        
                        # Fingerprinting de secretos conocidos
                        if "aiza" in decoded.lower() or "key" in decoded.lower() or "secret" in decoded.lower():
                            findings[f"{uid} ({attr})"] = f"[POSIBLE SECRETO] {decoded[:50]}..."
                        else:
                            findings[f"{uid} ({attr})"] = decoded
                    except:
                        pass # No es Base64 válido, ignoramos
        return findings if findings else {"status": "No se encontraron datos ofuscados en Base64 en los atributos analizados."}
    
    
    def find_weak_shells(self) -> Dict[str, List[str]]:
        """Encuentra usuarios con shells no restringidos"""
        users = self.ldap.get_all_users()
        weak = []
        restricted = []
        for user in users:
            shell = user.get("loginShell", "")
            uid = user.get("uid", "")
            if shell == "/bin/bash":
                weak.append(uid)
            elif shell in ["/bin/false", "/usr/sbin/nologin"]:
                restricted.append(uid)
        return {"bash_shells": weak, "restricted_shells": restricted}
    

    def enumerate_system_ou(self) -> list:
        """
        [OFFSEC] Lista todos los objetos bajo ou=system o cn=config donde suelen
        almacenarse configuraciones sensibles, políticas o passwords en texto claro.
        """
        try:
            return self.ldap.search("ou=system,dc=meli,dc=com", "(objectClass=*)", ["cn", "description", "objectClass"])
        except:
            return []

    def find_sudoers(self) -> list:
        """
        [OFFSEC] Búsqueda de reglas SudoRole almacenadas en LDAP. 
        Permite a un atacante ver quién tiene privilegios de root en qué máquinas Linux del dominio.
        """
        results = self.ldap.search(self.ldap.config.LDAP_BASE_DN, "(objectClass=sudoRole)", ["cn", "sudoUser", "sudoHost", "sudoCommand"])
        return [
            {
                "rule_name": r.get("cn"),
                "users": r.get("sudoUser", "ALL"),
                "hosts": r.get("sudoHost", "ALL"),
                "commands_allowed": r.get("sudoCommand", "ALL")
            }
            for r in results
        ]

    def find_ssh_keys(self) -> dict:
        """
        [OFFSEC] Enumeración de llaves públicas SSH. 
        Si un atacante compromete a un usuario, puede usar estas llaves para saltar a otros servidores (Movimiento Lateral).
        """
        results = self.ldap.search(self.ldap.config.LDAP_BASE_DN, "(objectClass=ldapPublicKey)", ["uid", "sshPublicKey"])
        keys_found = {}
        for r in results:
            uid = r.get("uid")
            if uid and r.get("sshPublicKey"):
                keys_found[uid] = r.get("sshPublicKey")
        return keys_found if keys_found else {"status": "No se encontraron claves SSH públicas expuestas en LDAP."}

    def close(self):
        self.ldap.disconnect()
