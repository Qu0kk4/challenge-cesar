# Ejemplos de Uso Completos
## Sistema de Agentes LDAP Auto-Adaptativos — Mercado Libre

Este documento muestra flujos de uso reales del sistema, organizados por nivel de complejidad.

---

## Cómo correr el agente

```bash
# 1. Asegurate de tener el servidor LDAP corriendo
cd open_ldap_files && ./setup-ldap.sh

# 2. Ejecutar el agente
poetry run python main.py
```

---

## Nivel 1 — Herramientas Estáticas (Respuesta Inmediata)

Estas consultas son respondidas por el Coordinator usando las herramientas pre-programadas de BaseTools sin llamar a la IA. Son instantáneas.

---

### Reconocimiento Inicial: Quien soy?
```
Tu consulta: quien soy

Procesando...
Resultado de quien_soy:
{
  'cn': 'admin',
  'mail': 'admin@meli.com',
  'title': 'System Administrator',
  'loginShell': '/bin/bash',
  'uid': 'admin'
}
```
> Uso ofensivo: Primera acción en cualquier operación de Red Team — identificar el contexto y los privilegios del bind LDAP.

---

### Enumeración de Grupos
```
Tu consulta: mis grupos

Procesando...
Resultado de mis_grupos:
['domain-admins', 'security-team', 'all-users']
```
> Uso ofensivo: Determinar a qué recursos y ACLs tiene acceso la cuenta comprometida.

---

### Auditoría de Shells Interactivas
```
Tu consulta: mostrame los usuarios con shells debiles

Procesando...
Resultado de shells_debiles:
{
  'bash_shells': ['admin', 'john.doe', 'alice.brown'],
  'restricted_shells': ['test.user', 'carlos.rodriguez']
}
```
> Uso ofensivo: Los usuarios con /bin/bash son objetivos prioritarios para movimiento lateral. Si se compromete su sesión SSH, dan acceso a una terminal real.

---

### Detección de Patrones de Contraseña (Password Spraying Prep)
```
Tu consulta: buscar patrones de password

Procesando...
Resultado de password_patterns:
{
  'weak_common': ['admin'],
  'default_password': ['john.doe', 'jane.smith', 'bob.wilson'],
  'strong_unique': ['carlos.rodriguez']
}
```
> Uso ofensivo: La categorización permite preparar una campaña de Password Spraying dirigida a las cuentas más vulnerables.

---

### Búsqueda de Secretos en Base64 (Steganografía LDAP)
```
Tu consulta: hay datos ocultos en base64

Procesando...
Resultado de esteganografia:
{
  'alice.brown (pager)': '[POSIBLE SECRETO] AIzaSyAjCtuFBO_TK2Gh################..'
}
```
> Uso ofensivo: Hallazgo crítico. La API Key de Gemini fue escondida en el atributo pager del usuario alice.brown en Base64. Esta herramienta la detecta automáticamente.

Decodificación manual de la API Key:
```python
import base64
base64.b64decode("QUl6YVN5QWpDdHVGQk9fVEsyR2hnRjV4d0tpcXM5ZnhXc25OLURB").decode()
# → 'AIzaSyAjCtuF##########################'
```

---

### Enumeración de Llaves SSH (Movimiento Lateral)
```
Tu consulta: claves ssh del dominio

Procesando...
Resultado de ssh_keys:
{
  'john.doe': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB...',
  'alice.brown': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQ...'
}
```
> Uso ofensivo: Si una de las claves privadas correspondientes es comprometida, el atacante puede saltar a cualquier servidor que acepte esa clave.

---

### Búsqueda de Reglas Sudoers (Escalamiento de Privilegios)
```
Tu consulta: buscar sudoers del dominio

Procesando...
Resultado de sudoers:
[
  {
    'rule_name': 'admins-full',
    'users': 'admin',
    'hosts': 'ALL',
    'commands_allowed': 'ALL'
  }
]
```
> Uso ofensivo: Identifica quién tiene root (ALL commands) en qué máquinas del dominio. Primer paso para escalar privilegios en un ataque post-explotación.

---

### Auditoría de Usuario (Compliance Check)
```
Tu consulta: auditar a alice.brown

Procesando...
Resultado de auditar_usuario:
REPORTE DE AUDITORÍA: alice.brown
----------------------------------------
[RIESGO ALTO] Login shell interactiva permitida.
[ADVERTENCIA] Atributo pager en uso (posible esteganografía).
----------------------------------------
VEREDICTO: NO-COMPLIANT (2 alertas de seguridad encontradas)
```
> Uso ofensivo/defensivo: El AuditorAgent combina múltiples checks para dar un veredicto de riesgo instantáneo sobre cualquier usuario del dominio.

---

## Nivel 2 — Auto-Generación de Herramientas (Gemini en Vivo)

Estas consultas no tienen una herramienta pre-programada. El sistema las detecta, le pide a Gemini 2.0 Flash que programe una función específica, y la ejecuta en tiempo real.

---

### Listar todos los correos y teléfonos del dominio
```
Tu consulta: listame todos los correos y teléfonos del dominio

Procesando...
[!] Solicitando al LLM (gemini/gemini-2.0-flash) que construya una herramienta para: 'listame todos los correos y teléfonos del dominio'...
[+] Código generado e inyectado con éxito. Ejecutando...

¡Nueva herramienta forjada!
Código Generado:
def dynamic_tool(ldap_client):
    base = f"ou=users,{ldap_client.config.LDAP_BASE_DN}"
    users = ldap_client.search(base, "(objectClass=inetOrgPerson)", ["cn", "mail", "telephoneNumber"])
    return [{"nombre": u.get("cn"), "correo": u.get("mail"), "telefono": u.get("telephoneNumber")} for u in users]

Resultado:
[
  {'nombre': 'admin', 'correo': 'admin@meli.com', 'telefono': '+1-555-0001'},
  {'nombre': 'John Doe', 'correo': 'john.doe@meli.com', 'telefono': '+1-555-0002'},
  {'nombre': 'Alice Brown', 'correo': 'alice.brown@meli.com', 'telefono': '+1-555-0005'},
  ...
]
```

---

### Listar todos los grupos del dominio
```
Tu consulta: cual es el nombre de todos los grupos

Procesando...
[!] Solicitando al LLM (gemini/gemini-2.0-flash) que construya una herramienta...
[+] Código generado e inyectado con éxito. Ejecutando...

¡Nueva herramienta forjada!
Código Generado:
def dynamic_tool(ldap_client):
    base = f"ou=groups,{ldap_client.config.LDAP_BASE_DN}"
    results = ldap_client.search(base, "(objectClass=groupOfNames)", ["cn", "description"])
    return [{"grupo": r.get("cn"), "descripcion": r.get("description")} for r in results]

Resultado:
[
  'admins', 'developers', 'managers', 'hr', 'finance', 'qa', 'it', 'all_users'
  ...
]
```

---

## Nivel 3 — Reset del Agente

Elimina todos los implantes (herramientas dinámicas) creadas en la sesión actual y vuelve al estado original.

```
Tu consulta: reset

Procesando...
El Agente ha regresado a su estado original. Archivo dynamic_tools.py purgado.
```

> Uso (OPSEC): En una operación de Red Team, al terminar la sesión activa, se eliminan los artefactos generados para no dejar huellas en el sistema.

---

## Correr los Tests

El sistema cuenta con una suite de **18 tests automatizados** que validan la salud del agente sin necesidad de conectarse al servidor LDAP real (usando Mocks). Esto garantiza que la lógica de la IA y el procesamiento de datos sean correctos.

```bash
# Correr todos los tests
poetry run pytest tests/ -v

# Correr solo los tests del agente y herramientas dinámicas
poetry run pytest tests/test_agent_and_dynamic_tools.py -v

# Correr solo los tests de herramientas base
poetry run pytest tests/test_base_tools.py -v
```


