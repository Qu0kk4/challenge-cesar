# Justificación del Enfoque Ofensivo (Red Team)
## Sistema de Agentes LDAP Auto-Adaptativos
---
El presente documento detalla la justificación táctica detrás de las herramientas pre-programadas (`BaseTools`) incluidas en este agente. En lugar de diseñar un asistente de administración tradicional de identidades, el sistema fue concebido como un **sensor de reconocimiento avanzado** para operaciones de Seguridad Ofensiva (Red Team).
La elección de las herramientas responde directamente a las fases clásicas de explotación de un entorno basado en OpenLDAP, haciendo hincapié en infraestructuras de e-commerce y fintech.
---
### 1. Reconocimiento de Identidad y Privilegios Base (`get_current_user_info` y `get_user_groups`)
* **Qué hace:** Consulta a la estructura LDAP para determinar la identidad actual del enlace (Bind request) y desentraña el mapa de Control de Acceso (ACLs) mediante la adscripción a grupos.
* **Justificación Ofensiva (Por qué):** En un entorno Fintech (como Mercado Libre), saber "quién sos y a dónde pertenecés" es el primer paso. Permite al atacante identificar rápidamente si la cuenta comprometida pertenece a unidades operativas críticas (ej: Finanzas, Fraud Prevention, DevOps). Mapear estos grupos significa saber exactamente qué usuarios tienen acceso a bases de datos de transacciones, repositorios de código clave, o infraestructura con requerimientos PCI-DSS.
### 2. Enumeración de Unidades Críticas (`enumerate_system_ou`)
* **Qué hace:** Apunta consultas específicas hacia la Unidad Organizativa de sistema (`ou=system`) buscando objetos ocultos y configuraciones de bajo nivel.
* **Justificación Ofensiva (Por qué):** Históricamente, las OUs de sistema son repositorios de deuda técnica y configuraciones intocables. Los atacantes buscan aquí Cuentas de Servicio (Service Accounts) y credenciales hardcodeadas en scripts de despliegue. Comprometer una de estas cuentas suele brindar acceso silencioso y persistente a repositorios críticos escapando al monitoreo común de los usuarios estándar.
### 3. Detección de Patrones de Contraseña (`find_password_patterns`)
* **Qué hace:** Correlaciona campos UID y nombres para detectar configuraciones inseguras, contraseñas por defecto o credenciales derivadas de la identidad pública del usuario.
* **Justificación Ofensiva (Por qué):** Prepara el terreno defensivo y ofensivo para campañas de **Password Spraying**. Al analizar la información pública del usuario (sin poseer sus hashes), el agente detecta configuraciones predecibles (ej: nombre+123). Esto reduce drásticamente el ruido de los ataques de fuerza bruta al apuntar únicamente a cuentas vectorialmente vulnerables que podrían exponer APIs de pagos o gateways internos.
### 4. Búsqueda de Esteganografía en Atributos (`extract_steganography`)
* **Qué hace:** Analiza los campos LDAP destinados a texto libre (`pager`, `description`, `info`) y detecta, decodifica y clasifica cadenas ocultas en Base64.
* **Justificación Ofensiva (Por qué):** Las malas prácticas de administración llevan frecuentemente al almacenamiento de secretos, API Keys o tokens en texto claro dentro de campos genéricos corporativos, a menudo ofuscadas de forma básica (Base64). Esta herramienta automatiza el descubrimiento de activos de infraestructura. En entornos Cloud, revelar un token oculto acá representa acceso automático a buckets S3 o vaults de despliegue. *(De hecho, en el entorno de prueba, permite descubrir la API Key deprecada del usuario alice.brown).*
### 5. Enumeración de Shells Débiles (`find_weak_shells`)
* **Qué hace:** Lista a los usuarios y clasifica qué tipo de consola de login tienen asignada en el atributo `loginShell`.
* **Justificación Ofensiva (Por qué):** Funciona para identificar de manera silenciosa cuentas que posean acceso a una terminal interactiva (como `/bin/bash` o `/bin/sh`) frente a shells restringidas (`/bin/false`). En la fase de **Movimiento Lateral**, identificar usuarios con iteración de bash habilitado en infraestructura cloud es crítico para asegurar un punto de anclaje (foothold) que permita luego pivotear hacia microservicios.
### 6. Enumeración de Reglas de Privilegio (`find_sudoers`)
* **Qué hace:** Busca de forma proactiva objetos que representen roles con permisos elevados o que dicten el comportamiento sudo.
* **Justificación Ofensiva (Por qué):** Es el mapa directo hacia el **Escalamiento de Privilegios**. Si un atacante logra comprometer la cuenta de un usuario estándar, esta herramienta permite evaluar ágilmente si la cuenta o su grupo poseen directivas `root` sobre servidores clave (como los de logging financiero o monitoreo), revelando el nivel de riesgo crítico de esa cuenta superficial.
### 7. Reconocimiento de Claves Públicas SSH (`find_ssh_keys`)
* **Qué hace:** Extrae y lista las llaves SSH públicas (`sshPublicKey`) de los empleados almacenadas de forma centralizada en el directorio.
* **Justificación Ofensiva (Por qué):** Permite construir una matriz de confianza para el **Movimiento Lateral**. Si un atacante roba una clave privada de un equipo expuesto o de la máquina de un desarrollador, el listado LDAP le indica automáticamente sobre qué servidores internos (nodos de Kubernetes, bases de datos o bastiones edge) puede inyectarse instantáneamente usando ese par de claves descubierto.
---
### Conclusión Estratégica
El sistema fue diseñado desde la concepción para demostrar que un LLM no es sólo una interfaz de procesamiento de lenguaje, sino un **analista ofensivo asíncrono**. Las herramientas base cubren metódicamente la recolección de información que cualquier ingeniero Red Team ejecutaría en la fase de pre-explotación sobre redes corporativas pesadas. Paralelamente, el Agente Generador (Orquestador LLM) proporciona escalabilidad infinita en tiempo real en caso de requerir el desarrollo in-situ de nuevas cargas de recolección frente a configuraciones LDAP personalizadas.
