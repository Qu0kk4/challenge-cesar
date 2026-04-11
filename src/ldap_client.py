import ldap
from typing import List, Dict, Optional
from src.config import Config

class LDAPClient:
    def __init__(self):
        self.conn = None
        self.config = Config()
        
    def connect(self) -> bool:
        try:
            self.conn = ldap.initialize(f"ldap://{self.config.LDAP_HOST}:{self.config.LDAP_PORT}")
            self.conn.simple_bind_s(self.config.LDAP_ADMIN_DN, self.config.LDAP_ADMIN_PASSWORD)
            return True
        except ldap.LDAPError as e:
            print(f"Error conectando a LDAP: {e}")
            return False
    
    def disconnect(self):
        if self.conn:
            self.conn.unbind_s()
    
    def search(self, base_dn: str, filter_str: str, attributes: List[str] = None) -> List[Dict]:
        if not self.conn:
            raise Exception("No conectado a LDAP")
        
        try:
            result = self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter_str, attributes)
            return [{attr: vals[0].decode() if isinstance(vals[0], bytes) else vals[0] 
                    for attr, vals in entry[1].items()} for entry in result]
        except ldap.LDAPError as e:
            print(f"Error en búsqueda: {e}")
            return []
    
    def get_user(self, uid: str) -> Optional[Dict]:
        users = self.search(f"ou=users,{self.config.LDAP_BASE_DN}", f"(uid={uid})")
        return users[0] if users else None
    
    def get_all_users(self) -> List[Dict]:
        return self.search(f"ou=users,{self.config.LDAP_BASE_DN}", "(objectClass=inetOrgPerson)")
    
    def get_all_groups(self) -> List[Dict]:
        return self.search(f"ou=groups,{self.config.LDAP_BASE_DN}", "(objectClass=groupOfNames)")
    
    def get_user_groups(self, uid: str) -> List[str]:
        user_dn = f"cn={uid},ou=users,{self.config.LDAP_BASE_DN}"
        groups = self.search(f"ou=groups,{self.config.LDAP_BASE_DN}", f"(member={user_dn})", ["cn"])
        return [g.get("cn", "") for g in groups]
