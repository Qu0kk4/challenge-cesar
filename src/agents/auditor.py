import logging
from src.tools.base_tools import BaseTools

logger = logging.getLogger("AuditorAgent")

class AuditorAgent:
    def __init__(self, ldap_client):
        self.ldap = ldap_client
        self.tools = BaseTools()

    def audit_user(self, username: str) -> str:
        """
        Audita a un usuario específico buscando violaciones de compliance.
        """
        logger.info(f"Iniciando auditoría de compliance para: {username}")
        user_info = self.tools.get_current_user_info(username)
        
        if not user_info or "uid" not in user_info:
            return f"❌ Auditoría fallida. Usuario '{username}' no encontrado."
            
        reporte = [f"🛡️ REPORTE DE AUDITORÍA: {username} 🛡️", "-"*40]
        riesgos = 0
        
        # 1. Chequeo de Shell
        shell = user_info.get("loginShell", "None")
        if shell in ["/bin/bash", "/bin/sh"]:
            reporte.append("🚨 [RIESGO ALTO] Login shell interactiva permitida.")
            riesgos += 1
        elif shell in ["/usr/sbin/nologin", "/bin/false"]:
            reporte.append("✅ [COMPLIANCE] Shell restringida correctamente.")
            
        # 2. Chequeo de contraseñas u ocultamiento
        if "pager" in user_info:
            reporte.append("⚠️ [ADVERTENCIA] Atributo 'pager' en uso (posible esteganografía).")
            riesgos += 1
            
        if "userPassword" in user_info:
            if user_info["userPassword"] in ["123456", "password", "itachi"]:
                reporte.append("🚨 [RIESGO EXTREMO] Contraseña trivial detectada.")
                riesgos += 1

        # Veredicto
        reporte.append("-" * 40)
        if riesgos == 0:
            reporte.append("🌟 VEREDICTO: COMPLIANT (Cumple políticas)")
        else:
            reporte.append(f"💀 VEREDICTO: NO-COMPLIANT ({riesgos} alertas de seguridad encontradas)")
            
        return "\n".join(reporte)
