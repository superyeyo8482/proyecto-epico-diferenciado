# 🌌 Integración LuxVinculum ↔ Quantum Forma

## Visión General

**LuxVinculum** (el bot de Telegram) y **Quantum Forma** (el núcleo financiero, de seguridad y gestión) se comunicarán para ofrecer funcionalidades avanzadas. LuxVinculum actúa como la interfaz de usuario, mientras que Quantum Forma ejecuta las operaciones de alto nivel.

---

## 1. Flujo de Comunicación General

1.  Usuario envía un comando o mensaje a LuxVinculum (Telegram).
2.  LuxVinculum identifica si la acción requiere una función de Quantum Forma.
3.  Si es así, LuxVinculum realiza una llamada a la API de Quantum Forma.
4.  Quantum Forma procesa la solicitud (validación, cifrado, consulta de saldo, etc.).
5.  Quantum Forma devuelve la respuesta a LuxVinculum.
6.  LuxVinculum formatea y envía la respuesta al usuario.

---

## 2. Funciones Clave de Quantum Forma

| Función | Descripción | Datos de Entrada | Datos de Salida |
| :--- | :--- | :--- | :--- |
| **Mensajes Autodestructivos** | Envía un mensaje que se elimina después de ser leído o tras un tiempo determinado. | 	exto, 	iempo_vida (segundos), chat_id | mensaje_id, estado |
| **Gestión de ImageTempCoin** | Consulta de saldo, transferencia y administración de criptomonedas. | ccion (consultar, enviar, recibir), cantidad, destino | saldo, hash_transaccion |
| **Comprobación de Voz** | Valida la identidad del usuario mediante su voz para llamadas privadas. | udio_base64, usuario_id | erificado (booleano) |
| **Llamadas Privadas** | Inicia y gestiona llamadas de voz cifradas entre usuarios. | usuario_origen, usuario_destino | estado_llamada, id_sesion |
| **StampCoin Activa** | Activa una StampCoin para mensajes de alto nivel de seguridad. | usuario_id, 
ivel_seguridad | stampcoin_id, codigo_activacion |

---

## 3. Arquitectura de Comunicación

LuxVinculum y Quantum Forma se comunicarán mediante una **API REST** sobre HTTPS.

- **Formato de Datos:** JSON.
- **Autenticación:** Las peticiones de LuxVinculum a QF incluirán una **API Key** secreta para autorización.
- **Flujo Asíncrono:** Las operaciones largas (como llamadas) se manejarán con un sistema de colas para no bloquear al usuario.

### Endpoints Propuestos

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| POST | /api/seguridad/mensaje_autodestructivo | Envía un mensaje autodestructivo. |
| GET | /api/finanzas/saldo | Consulta el saldo de ImageTempCoin. |
| POST | /api/finanzas/transferir | Realiza una transferencia de ImageTempCoin. |
| POST | /api/llamadas/iniciar | Inicia una llamada privada. |
| POST | /api/stampcoin/activar | Activa una StampCoin. |

---

## 4. Seguridad

- **Cifrado:** Todas las comunicaciones entre LuxVinculum y QF usarán TLS (HTTPS).
- **Autenticación:** LuxVinculum tendrá un par de credenciales (API Key + Secret) para autenticarse en QF.
- **Validación:** QF validará todas las solicitudes para prevenir abusos.

---

## 5. Próximos Pasos

1.  Definir el esquema detallado de la API de Quantum Forma.
2.  Implementar los endpoints principales en Quantum Forma.
3.  Modificar LuxVinculum (Boot.py) para consumir la API de QF.
4.  Probar la integración de forma local.
5.  Desplegar y probar en el entorno de producción.

---

*Este documento es el punto de partida para la integración entre LuxVinculum y Quantum Forma.*
