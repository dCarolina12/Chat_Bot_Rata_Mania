---
tipo: bitacora-clase
curso: Electiva II
periodo: EAM-2026II
equipo: Equipo_Pacheco_Farfan_chat_bot
corte: 2
semana: semana 4
clase: clase 9
fecha: 2026-10-23
estado: en-progreso
tags:
  - chatbots
  - bitacora
---

# Bitácora — Clase [9- entrega segundo corte]

> [!tip] Cómo usar esta plantilla
> Duplica esta nota al finalizar cada clase y nómbrala `C##_AAAA-MM-DD_Tema`. Completa los campos entre corchetes y conserva enlaces verificables.

## 1. Datos de la sesión

| Campo    | Registro                 |
| -------- | ------------------------ |
| Tema     | Chat bot con IA          |
| Objetivo | Hacer un chat bot con IA |
| Proyecto | Rata Mania - Cyberrat    |
| Inicio   | [Hora]                   |
| Cierre   | [Hora]                   |

## 2. Participación y responsabilidades

| Integrante             | Asistió | Rol de la clase             | Responsabilidad asumida | Aporte verificable                             |
| ---------------------- | :-----: | --------------------------- | ----------------------- | ---------------------------------------------- |
| Diana Carolina Pacheco |   Sí    | Administradora del proyecto | Desarrollar proyecto    | archivo de código y requerimientos funcionales |
| Jhon Edison Farfan     |   Sí    | Administradora del proyecto | Desarrollar proyecto    | archivo de código y requerimientos funcionales |

## 3. Reto aplicado al proyecto

### Funcionalidad trabajada

Nombre del chatbot: Cyberratt

Dominio: hacer Perdidos locales, consultas de disponibilidad y cancelar pedidos

Problema: En Armenia es complejo encontrar información acerca de ratas domésticas ya que al parecer no hay criaderos o formas intuitivas de encontrar información 

Usuario objetivo: Personas en busca de animales exóticos 

Objetivo: Hacer más fácil la consulta de disponibilidad de ratas domésticas localmente 

Capacidades (3–5): pedir, consultar y cancelar 

Sí puede / No puede: 

Patrón adaptado: INFORMAR + CONVERSAR + RECORDAR + CONSULTAR DISPONIBILIDAD + CREAR + CONSULTAR + CANCELAR

Proceso (pasos): solicitar → completar datos → disponibilidad → confirmar → registrar → código

### Criterios de aceptación

- [ ] [Criterio 1]
- [ ] [Criterio 2]
- [ ] [Criterio 3]

### Archivos o componentes modificados

- `[negocio.json]`: [lógica de negocio personalizada con rata mania ]
- `[main.py]`: [adaptación de métodos y endpoints para mejorar logica]
- [[reversas.json]]: [formateado ] 
-  `[docker-compose.yml]`: [configuracion para despleje del servidor flowised]
- -  `[prompt_sistema.txt]`: [modificación de instrucciones para el modelo de IA ]

- `[consulta_llm.py]`: [conexion de groq con la FastApi ]

- `[almacen_sqlite.py - main_sqlite_ejemplo.py ]`: No se modificaron encontramos una manera de manejar la base de datos mas simple y fácil que metiéndole mas código a nuestro proyecto

- `[app_gradio.py]`: Se organizo el código y se simplifico para adaptarse a el proyecto de ratas de nosotros, su nombre como gradio_e.py 

## 4. Decisiones técnicas


| Decisión                            | Razón                                                                                  | Alternativa descartada         |
| ----------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------ |
| modificamos archivo consulta_llm.py | modificamos el archivo base que envió el profesor con los datos sobre nuestro proyecto | [Qué otra opción consideraron] |

| Decisión                                                                                                                                                                                             | Razón                                                                                                                                                                                                                       | Alternativa descartada     |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| Decidimos hacer la búsqueda y filtración por medio de una Shell Linux usando bash scripting, usando como script automatizado de extraccion de datos y al mismo tiempo los inserta en la base de dato | Porque pensamos que nuestro código esta tan cargado y cada vez mas largo que en algún punto sabemos que no lo entenderemos, esa fue una solución mas corta y rápida, funciona igual como los archivos que envio el profesor | Los archivos del profesor  |

| Decisión                     | Razón                                                                                                                                                                                                                                  | Alternativa descartada                         |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Adaptar el proyecto a docker | para manejar los servicios api y gradio por separado, organizado y todo en un comando central para su despliegue. Adicionalmente de esa manera se podrá ejecutar en diferentes sistemas y los scripts seguirán teniendo compatibilidad | ejecución  desde del entorno virtual de python |

## 5. Problemas y soluciones

| Problema encontrado | Causa identificada | Solución aplicada | ¿Cómo se verificó? |
|---|---|---|---|
| [Descripción] | [Causa] | [Solución] | [Prueba o evidencia] |

| Problema encontrado    | Causa identificada                                                                                                                               | Solución aplicada                                                                                                      | ¿Cómo se verificó?                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| Politica de privacidad | como flowise se despliega con docker hay un problema de seguridad al comunicarse a direcciones locales incluso cuando el cotafuegos esta abierto | tunel de comunicacion de HTTP a HTTPS al puerto de la API dando asi un despliegue del servicio por fuera de la maquina | ![[Pasted image 20260914114620.png]] |

| Problema encontrado | Causa identificada | Solución aplicada | ¿Cómo se verificó?   |
| ------------------- | ------------------ | ----------------- | -------------------- |
| ninguno             | [Causa]            | [Solución]        | [Prueba o evidencia] |

| Problema encontrado | Causa identificada | Solución aplicada | ¿Cómo se verificó?   |
| ------------------- | ------------------ | ----------------- | -------------------- |
| NINGUNO             | [Causa]            | [Solución]        | [Prueba o evidencia] |



## 6. Evidencias

| Tipo                    | Descripción                          | Enlace o ruta            |
| ----------------------- | ------------------------------------ | ------------------------ |
| commit del archivo      | ![[Pasted image 20260914114931.png]] | negocio.json             |
| Captura                 |                                      | [Ruta relativa]          |
| Demo de la API          | ![[Pasted image 20260914115241.png]] | desplegado en la maquina |
| Código principal de API | ![[Pasted image 20260914115341.png]] | main.py                  |

| Tipo                 | Descripción                                                                                                                                                                                                                                |                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------- |
| Ejecucion<br>Captura | se desplego el archivo main.py en el entorno virtual de python<br>por otro lado se ejecuta el archivo consulta_llm.py para que este simule el chat desde consola, aqui se evidencia como se hace un pequeño registro acerca de una reserva | ![[ratas.png]]         |
| Captura              | Cambios en el archivo consulta_llm.py y su implementación<br>en especial la constante INSTRUCCIONES que le dice al modelo como deberia de comportarse e interpretar todas las respuestas json del servicio main.py                         | [![[consulta (1).png]] |

| Tipo                                                                                                                                                                                                                                                                                                                                                            | Descripción                          | Enlace o ruta                       |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ----------------------------------- |
| evidencia de datos persistentes en sqlite                                                                                                                                                                                                                                                                                                                       | ![[Pasted image 20261016172501.png]] | Ruta carpeta raiz del proyecto      |
| Captura del script que automatiza las sentencias sql para guardar y cancelar manteniendo actualizada la base de datos                                                                                                                                                                                                                                           | ![[Pasted image 20261016172530.png]] | Ruta carpeta raiz del proyecto      |
| captura de codigo:<br>- metodos principales para consultar los datos, guardar y cancelar.<br>asegurándose de que se ejecute un llamado a la base de datos unicamente cuando sea necesario despues de actualizar las reservas asegurando su optimizacion y persistencia con offset integrado dentro del script                                                   | ![[Pasted image 20261016172541.png]] | Ruta carpeta raiz del proyecto      |
| evidencia de funcionamiento de base de datos:<br>-se encierra en rojo la conversación y los registros dentro de la base de datos que fueron agregados y actualizados por medio de las peticiones del usuario<br><br>-se encierra en amarillo los datos claves para asi demostrar la persistencia y las modificaciones en tiempo real dentro de la base de datos | ![[Pasted image 20261016172554.png]] | Ruta carpeta raiz del proyecto      |
| evidencia del esquema basico de la tabla reserva dentro de la base de datos compatible con el esquema anterior del formato JSON                                                                                                                                                                                                                                 | ![[Pasted image 20261016172607.png]] | dentro de la base de datos ratas.db |

| Tipo                                                                                                                              | Descripción                                    | Enlace o ruta                         |
| --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------- |
| Aplicacion con gradio del chat bot                                                                                                | ![[Captura de pantalla 2026-10-17 163908.png]] | Escritorio                            |
| Evidencia de inicio del proyecto usando docker compose                                                                            | ![[Captura de pantalla 2026-10-17 164118.png]] | Directorio docker dentro del proyecto |
| Servicio api corriendo en el puerto 8011                                                                                          | ![[Captura de pantalla 2026-10-17 164143.png]] | Directorio docker                     |
| Dentro de la shell del servicio api, listando los archivos del proyecto                                                           | ![[Captura de pantalla 2026-10-17 164320.png]] | Servicio api                          |
| Descargando sqlite para administración de la base de datos (dependencias especificas dentro del contenedor para usar en shell)    | ![[Captura de pantalla 2026-10-17 164754.png]] | Servicio api                          |
| Base de datos antes del registro desde la aplicación gradio                                                                       | ![[Captura de pantalla 2026-10-17 164918.png]] | Servicio api                          |
| Registro de un nuevo usuario llamado Piruleto y lo que desea reservar                                                             | ![[Captura de pantalla 2026-10-17 165131.png]] | Aplicación gradio                     |
| Registro de la fecha y hora de la reserva                                                                                         | ![[Captura de pantalla 2026-10-17 165154.png]] | Aplicación gradio                     |
| Confirmación de reserva y con datos adicionales como el código de la reserva registrada (este código sirve para cancelar reserva) | ![[Captura de pantalla 2026-10-17 165217.png]] | Aplicación gradio                     |
| Evidencia del registro dentro de la base de datos a nombre de Piruleto                                                            | ![[Captura de pantalla 2026-10-17 165246.png]] | Servicio api                          |
| Cierre de los contenedores (servicio api y servicio gradio detenidos)                                                             | ![[Captura de pantalla 2026-10-17 165419.png]] | Carpeta docker                        |

## 7. Uso de inteligencia artificial

> [!important] Registrar la IA no reemplaza la explicación técnica. El equipo debe verificar, adaptar y comprender cualquier resultado utilizado.

| Herramienta    | Objetivo o pregunta                                                                   | Qué se utilizó                                      | Cómo se verificó                                                | Qué se modificó                        |
| -------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------- |
| Agente copilot | Comunicar los endpoints de main.py con las solicitudes enviadas desde consulta_llm.py | modificación del código fuente por parte del agente | los logs del servicio principal muestra correcto funcionamiento | los archivos main.py y consulta_llm.py |

| Herramienta                                                                                | Objetivo o pregunta  | Qué se utilizó       | Cómo se verificó  | Qué se modificó     |
| ------------------------------------------------------------------------------------------ | -------------------- | -------------------- | ----------------- | ------------------- |
| **No se utilizó inteligencia artificial en esta sesión, solo preguntas basicas en google** | [Solicitud resumida] | [Aporte aprovechado] | [Prueba o fuente] | [Adaptación propia] |

| Herramienta | Objetivo o pregunta                                                                                                                              | Qué se utilizó | Cómo se verificó            | Qué se modificó |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- | --------------------------- | --------------- |
| Gemini      | Limpiar el código dado y simplificar eliminado módulos no necesarios y para pasar los metodos del archivo consulta_llm.py al archivo gradio_e.py | chat de gemini | Se ejecuto para las pruebas | gradio_e.py     |
Si no se utilizó IA, escribir: **No se utilizó inteligencia artificial en esta sesión.**

## 8. Defensa técnica y retroalimentación

| Campo | Registro |
|---|---|
| Integrante que defendió | [Nombre] |
| Pregunta recibida | [Pregunta] |
| Respuesta resumida | [Respuesta] |
| Retroalimentación docente | [Observación] |
| Mejora acordada | [Acción concreta] |

## 9. Aprendizajes

- **Concepto comprendido:** [Aprendizaje principal]
- **Algo que aún genera duda:** [Duda pendiente]
- **Qué haríamos diferente:** [Mejora del proceso]

## 10. Revisión antes de entregar

- [x] Todos los integrantes registraron un aporte verificable.
- [x] Los enlaces y rutas de evidencia funcionan.
- [ ] Los criterios de aceptación están actualizados.
- [x] El uso de IA fue declarado y verificado.
- [x] El equipo puede explicar las decisiones registradas.

