# Justificación del Enfoque Ofensivo (Red Team)
## Sistema de Agentes LDAP Auto-Adaptativos

El presente documento detalla la justificación táctica detrás de las herramientas pre-programadas (`BaseTools`) incluidas en este agente. En lugar de diseñar un asistente de administración tradicional de identidades, el sistema fue concebido como un **sensor de reconocimiento avanzado** para operaciones de Seguridad Ofensiva (Red Team).

La elección de las herramientas responde directamente a las fases clásicas de explotación de un entorno basado en OpenLDAP.

---

### 1. Búsqueda de Steganografía en Atributos (`extract_steganography`)
* **Qué hace:** Analiza los campos LDAP destinados a texto libre (`pager`, `description`, `info`) y detecta, decodifica y clasifica cadenas ocultas en Base64.
* **Justificación Ofensiva (Por qué):** Históricamente, las malas prácticas de administración llevan al almacenamiento de secretos, API Keys o contraseñas en texto claro dentro de los entornos coorporativos, a menudo ofuscadas de forma básica (Base64). Esta herramienta automatiza el descubrimiento de estos activos de alto valor. De hecho, en el entorno de prueba, permite descubrir la API Key deprecada del usuario *alice.brown*.

### 2. Enumeración de Shells Débiles (`find_weak_shells`)
* **Qué hace:** Lista a los usuarios y clasifica qué tipo de consola de login tienen asignada en el atributo `loginShell`.
* **Justificación Ofensiva (Por qué):** Identificar de manera silenciosa cuentas que posean acceso a una terminal interactiva (como `/bin/bash` o `/bin/sh`) frente a shells restringidas (como `/bin/false`). En la fase de **Movimiento Lateral**, comprometer a un usuario con acceso interactivo es crítico para asegurar un punto de anclaje (foothold) robusto en la infraestructura.

### 3. Enumeración de Reglas de Privilegio (`find_sudoers`)
* **Qué hace:** Busca de forma proactiva objetos del tipo `sudoRole` que se encuentren vinculados al LDAP.
* **Justificación Ofensiva (Por qué):** Mapear la ruta hacia el **Escalamiento de Privilegios**. Si un atacante logra comprometer la cuenta de un usuario estándar, esta herramienta permite evaluar rápidamente si dicha cuenta posee directivas `root` o permisos de ejecución sudo sobre otros servidores del dominio, revelando el nivel de riesgo real de una cuenta.

### 4. Detección de Patrones de Contraseña (`find_password_patterns`)
* **Qué hace:** Correlaciona campos UID y nombres para detectar configuraciones inseguras, contraseñas por defecto o credenciales derivadas de la identidad del usuario.
* **Justificación Ofensiva (Por qué):** Prepara el terreno para campañas de **Password Spraying**. Al analizar la información pública del usuario (sin poseer sus hashes), el agente detecta configuraciones débiles, reduciendo drásticamente el ruido de los ataques de fuerza bruta al apuntar únicamente a cuentas vectorialmente vulnerables.

### 5. Reconocimiento de Claves Públicas SSH (`find_ssh_keys`)
* **Qué hace:** Extrae y lista los atributos vinculados a llaves SSH públicas de los empleados almacenadas centralmente en LDAP.
* **Justificación Ofensiva (Por qué):** Permite construir un mapa de confianza de **Movimiento Lateral**. Si un atacante roba una clave privada en el equipo de un desarrollador, esta herramienta indica exactamente en qué otros equipos de la red corporativa puede inyectarse usando ese par de claves.

---

### Conclusión Estratégica
El sistema fue estructurado para demostrar que un LLM no es sólo una interfaz de procesamiento de texto, sino un **analista ofensivo asíncrono**. Las herramientas base cubren la recolección de información crítica que cualquier ingeniero de seguridad solicitaría en la etapa de pre-explotación. Paralelamente, el Agente Generador proporciona escalabilidad infinita en tiempo real en caso de hallar componentes de infraestructura previamente desconocidos.
