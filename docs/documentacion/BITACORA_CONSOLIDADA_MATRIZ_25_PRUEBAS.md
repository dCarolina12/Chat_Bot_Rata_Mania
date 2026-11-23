---
tipo: documentacion-final
proyecto: Cyberratt (Rata Mania)
corte: 3
estado: Finalizado
integrantes:
  - Diana Carolina Pacheco Castiblanco
  - Jhon Edison Farfán Aranzazu
tags:
  - entrega-final
  - chatbots
  - telegram
---
---

#  Bitácora Consolidada: Cyberratt (Rata Mania)

> [!abstract] Resumen del Proyecto
> **Cyberratt** es un chatbot diseñado para facilitar la consulta de disponibilidad, pedidos y cancelación de ratas domésticas en Armenia. Esta bitácora documenta la evolución completa del sistema, desde sus primeras versiones con Flowise, pasando por Gradio, hasta la arquitectura final en Telegram con botones interactivos y persistencia en SQLite.

---

## 1. Problema, Usuarios y Alcance

> [!info] Contexto del Proyecto

- **Problema:** En Armenia es complejo encontrar información acerca de ratas domésticas, ya que no hay criaderos o canales de atención intuitivos para consultar localmente.
- **Usuario Objetivo:** Personas en busca de animales exóticos (ratas domésticas) a nivel local
- **Objetivo:** Hacer más fácil la consulta de disponibilidad, pedir y cancelar pedidos
- **Límites del Servicio:** El bot puede informar, consultar disponibilidad, crear reservas y cancelar. **No puede** compartir información privada de otros usuarios.

## 2. Arquitectura y Archivos

> [!quote] Recorrido de la arquitectura final

**Recorrido de una solicitud en la versión final:**
1. **Telegram (`telegram.py`):** Captura el mensaje del usuario desde la app móvil en tiempo real a través del token de BotFather
2. **FastAPI (`main.py`):** Recibe la solicitud y gestiona la lógica central y los endpoints del sistema
3. **Modelo de Lenguaje (`consultaa.py`):** Conectado a la API de Groq, interpreta la intención del usuario guiado por el `prompt_sistema.txt` y responde en formato JSON.
4. **Base de Datos ( `ratas.db`):** Verifica el inventario en `negocio.json` y guarda los registros de manera persistente.

## 3. Contexto, Memoria y Estado

> [!example] Manejo de usuarios concurrentes

- **Separación de cuentas:** Al migrar a Telegram, el sistema utiliza el `chat_id` nativo de cada usuario. Esto aísla el historial de conversación, evitando que los pedidos de un cliente se mezclen con los de otro cliente.
- **Persistencia ante reinicios:** La base de datos en SQLite asegura que, incluso si los contenedores de Docker o los scripts se detienen, los pedidos confirmados y cancelados se mantengan intactos y actualizados.

## 4. Operaciones y Validaciones

> [!check] Reglas de Negocio Implementadas

- **Disponibilidad y Creación:** El usuario solicita información, completa datos, el bot verifica la disponibilidad, confirma y registra entregando un código único.
- **Cancelación:** Con el código de reserva proporcionado al momento del registro, el usuario puede cancelar su pedido.
- **Interfaz Guiada (Botones):** Se implementaron botones interactivos al final de los flujos principales (ej. para confirmar o cancelar). Esto facilita la respuesta, evita errores de escritura por parte del usuario y mantiene el proceso estructurado y rápido.

## 5. Evolución y Decisiones Técnicas

> [!abstract] Justificación de la Arquitectura durante los 3 cortes

| Versión     | Herramienta         | Razón de la decisión y evolución                                                                                                                                                                                                                                                                    |
| :---------- | :------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Corte 1** | **Flowise**         | Se utilizó para un despliegue inicial rápido, pero presentó problemas de seguridad (política de privacidad) y bloqueo de firewall local.                                                                                                                                                            |
| **Corte 2** | **Gradio + Docker** | Migramos a código propio (FastAPI + Groq) y usamos Gradio para la interfaz visual `gradio_e.py`, contenerizando todo en Docker para evitar conflictos de dependencias. Manejamos la DB con bash scripts                                                                                             |
| **Corte 3** | **Telegram**        | **Decisión Final:** Desacoplamos la interfaz web para usar Telegram (`telegram.py`) Decidimos integrar **botones interactivos** en el chat para mejorar la Experiencia de Usuario (UX), guiando la conversación de manera más amigable y evitando que el LLM se confunda con entradas mal escritas. |

## 6. Fallos y Correcciones

> [!bug] Problemas resueltos en el semestre

| Fallo encontrado                           | Causa identificada                                                                | Solución aplicada                                                                                                                       |
| :----------------------------------------- | :-------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------- |
| **Bloqueo de red en despliegue (Corte 1)** | Problema de seguridad al comunicarse con direcciones locales en Docker (Flowise). | Implementación de un túnel de comunicación de HTTP a HTTPS, desplegando el servicio fuera de la máquina local.                          |
| **Código espagueti en DB (Corte 2)**       | El archivo `main.py` se estaba sobrecargando con las peticiones SQL.              | Se usó un script automatizado para la extracción y filtración de datos, asegurando un llamado óptimo a la DB solo cuando sea necesario. |

---

## 7. MATRIZ DE 25 PRUEBAS (Integración Final)

> [!tip] Casos de prueba en Telegram


| Grupo / ID               | Entrada del Usuario                                               | Resultado Esperado                                                                                                                                                       | Resultado Obtenido                                                                                                                                                                            | Evidencia (Sí/No)                    |
| :----------------------- | :---------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------- |
| **Normal T01**           | "Quiero adoptar una rata doméstica"                               | El Bot dice los productos disponibles                                                                                                                                    | ¿Qué producto o adopción te interesa? Opciones: rata_husky, rata_dumbo, rata_hairless, jaula_equipada, alimento_premium.                                                                      | ![[Pasted image 20261122191510.png]] |
| **Normal T02**           | "Quiero una rata_dumbo"                                           | el bot pide la fecha para la reserva                                                                                                                                     | ¿Para qué fecha (AAAA-MM-DD) deseas agendar tu visita?                                                                                                                                        | ![[Pasted image 20261122191904.png]] |
| **Normal T03**           | "la quiero para el dia 2026-11-24"                                | El sistema busca la fecha y el bot da los horarios disponibles                                                                                                           | Horarios disponibles para el 2026-11-24: 09:00, 09:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30. ¿A qué hora prefieres? | ![[Pasted image 20261122192014.png]] |
| **Normal T04**           | Usuario hace clic en el botón "Confirmar Reserva"                 | El bot detecta la acción del botón, procesa la confirmación en SQLite sin pedir más texto y solo manda el resumen de la reserva.                                         | Reserva registrada. Código: PN-A1E465E6. carolina tiene agendado rata_dumbo el 2026-11-24 a las 15:00.                                                                                        | ![[Pasted image 20261122192206.png]] |
| **Normal T05**           | "Quiero cancelar mi reserva, con el codigo PN-XYZ"                | el bot avisa que reserva pertenece al codigo y si desea cancelarla o no                                                                                                  | Vas a cancelar la reserva PN-7B2B5983 (Jhon — jaula_equipada el 2027-01-02 a las 17:00). Responde CONFIRMAR para proceder o ABORTAR para cancelar.                                            | ![[Pasted image 20261122192351.png]] |
| **Normal T06**           | Usuario hace clic en el botón "Confirmar para cancelar respuesta" | mensaje de confirmación a la hora de cancelar                                                                                                                            | Reserva cancelada. (PN-7B2B5983)                                                                                                                                                              | ![[Pasted image 20261122192505.png]] |
| **Ambiguas T07**         | "Quiero una" sin contexto                                         | el bot vuelve a preguntar esta vez con énfasis en que producto desea                                                                                                     | ¿Qué producto o adopción te interesa? Opciones: rata_husky, rata_dumbo, rata_hairless, jaula_equipada, alimento_premium.                                                                      | ![[Pasted image 20261122202658.png]] |
| **Ambiguas T08**         | Fecha incompleta                                                  | el bot vuelve a preguntar esta vez con énfasis en que fecha desea                                                                                                        | ¿Para qué fecha (AAAA-MM-DD) deseas agendar tu visita?                                                                                                                                        | ![[Pasted image 20261122202718.png]] |
| **Ambiguas T9**          | Cancelación sin codigo                                            | el bot pregunta los datos que hacen falta para la cancelacion                                                                                                            | ¿Cuál es el código de la reserva que deseas cancelar?                                                                                                                                         | ![[Pasted image 20261122203202.png]] |
| **Contexto T10**         | Cambio de preferencia                                             | el bot continua la charla con normalidad remplazando el nuevo producto en la reserva                                                                                     | ¿Para qué fecha (AAAA-MM-DD) deseas agendar tu visita?                                                                                                                                        | ![[Pasted image 20261122202616.png]] |
| **Contexto T11**         | Actualizar fecha en medio del contexto                            | el bot no empieza desde cero, mantiene la información y actualiza únicamente el dato cambiado y lo vuelve a confirmar                                                    | Resumen: Pepe — rata_dumbo el 2026-12-31 a las 09:30. Responde CONFIRMAR para guardar o ABORTAR para descartar.                                                                               | ![[Pasted image 20261122203754.png]] |
| **Contexto T12**         | Actualizar hora en medio del contexto                             | el bot no empieza desde cero, mantiene la información y actualiza únicamente el dato cambiado y lo vuelve a confirmar (De 9 am pasa a 10:30 am sin volver a pedir datos) | Resumen: Jhon — rata_husky el 2026-12-31 a las 10:30. Responde CONFIRMAR para guardar o ABORTAR para descartar.                                                                               | ![[Pasted image 20261122204331.png]] |
| **Contexto T13**         | Actualizar nombre en medio del contexto                           | el bot no empieza desde cero, mantiene la información y actualiza únicamente el dato cambiado y lo vuelve a confirmar                                                    | Resumen: Mariano — jaula_equipada el 2026-12-31 a las 14:30. Responde CONFIRMAR para guardar o ABORTAR para descartar.                                                                        | ![[Pasted image 20261122215921.png]] |
| **Fuera de dominio T14** | "Quiero un perrito loco saltarin 😘"                              | El bot decide enviar solo lo que tiene disponible en su dominio sin sobre explicar nada                                                                                  | ¿Qué producto o adopción te interesa? Opciones: rata_husky, rata_dumbo, rata_hairless, jaula_equipada, alimento_premium.                                                                      | ![[Pasted image 20261122193743.png]] |
| **Fuera de dominio T15** | "hazme un ensayo de la revolucion francesa"                       | El bot decide enviar solo lo que tiene disponible en su dominio sin sobre explicar nada                                                                                  | ¿Qué producto o adopción te interesa? Opciones: rata_husky, rata_dumbo, rata_hairless, jaula_equipada, alimento_premium.                                                                      | ![[Pasted image 20261122193630.png]] |
| **Fuera de dominio T16** | "Cuanto cuesta el GTA VI"                                         | El bot decide enviar solo lo que tiene disponible en su dominio sin sobre explicar nada                                                                                  | ¿Qué producto o adopción te interesa? Opciones: rata_husky, rata_dumbo, rata_hairless, jaula_equipada, alimento_premium.                                                                      | ![[Pasted image 20261122193808.png]] |
| **Negocio T17**          | Pedir producto                                                    | el bot dará la información de lo que tiene en la tienda                                                                                                                  | En Rata mania tenemos: rata_husky, rata_dumbo, rata_hairless, jaula_equipada, alimento_premium. ¿Cuál te interesa o deseas agendar una visita?                                                | ![[Pasted image 20261122220808.png]] |
| **Negocio T18**          | Agendar fecha                                                     | el bot preguntara para que fecha se desea la reserva                                                                                                                     | ¿Para qué fecha (AAAA-MM-DD) deseas agendar tu visita?                                                                                                                                        | ![[Pasted image 20261122220810.png]] |
| **Negocio T19**          | Agendar horario                                                   | el bot dará los horarios disponibles según la fecha escogida                                                                                                             | Horarios disponibles para el 2026-12-12: 09:00, 09:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30. ¿A qué hora prefieres? | ![[Pasted image 20261122221152.png]] |
| **Negocio T20**          | Nombre de la persona que queda la reserva/registro                | el bot preguntara el nombre de quien es la reserva/registro                                                                                                              | ¿A nombre de quién hacemos el registro?                                                                                                                                                       | ![[Pasted image 20261122221254.png]] |
| **Negocio T21**          | Confirmación de la reserva                                        | el bot dara el resumen de la reserva si fue confirmada                                                                                                                   | Reserva registrada. Código: PN-22FE878C. Papoi tiene agendado rata_husky el 2026-12-12 a las 09:30.                                                                                           | ![[Pasted image 20261122221550.png]] |
| **Error T22**            | Agendar en un año que ya paso                                     | el bot envia un mensaje de error generico                                                                                                                                | Error HTTP 422. Asegúrate de que FastAPI (uvicorn) esté corriendo.                                                                                                                            | ![[Pasted image 20261122200422.png]] |
| **Error T23**            | Agendar en un mes que no existe                                   | el bot envia un mensaje de error generico                                                                                                                                | Error HTTP 500. Asegúrate de que FastAPI (uvicorn) esté corriendo.                                                                                                                            | ![[Pasted image 20261122200706.png]] |
| **Error T24**            | Agendar en una hora no disponible                                 | el bot contesta diciendo que el horario no esta disponible sin dar mucho detalle                                                                                         | Ese horario no está disponible: el servicio solicitado en la fecha elegida a las esa hora. Elige otra hora o fecha libre y vuelve a confirmar.                                                | ![[Pasted image 20261122200740.png]] |
| **Error T25**            | Texto sin sentido                                                 | El bot no se rompe, sino que responde que no entendió el mensaje y le ofrece las opciones principales                                                                    | ¿Qué producto o adopción te interesa? Opciones: rata_husky, rata_dumbo, rata_hairless, jaula_equipada, alimento_premium.                                                                      | ![[Pasted image 20261122222955.png]] |


---

## 8. Uso de Inteligencia Artificial (Semestre)
| Herramienta        | Qué se utilizó y modificó                                                                                                     |
| :----------------- | :---------------------------------------------------------------------------------------------------------------------------- |
| **GitHub Copilot** | Se utilizó para estructurar la comunicación de los endpoints de `main.py` con las solicitudes enviadas desde `consultaa.py`.  |
| **Gemini**         | Se usó para limpiar y simplificar el código base, eliminando módulos innecesarios al pasar de `consultaa.py` a `gradio_e.py`. |
