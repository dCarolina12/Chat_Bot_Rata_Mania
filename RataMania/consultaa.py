"""Lógica del chatbot adaptada para Rata Manía (FastAPI /chat endpoint).

Groq interpreta la intención y extrae los datos, y la FastAPI de Rata Manía
maneja el flujo conversacional, las sesiones y el almacenamiento.
"""

import json
import os
import re
from getpass import getpass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Apunta a tu FastAPI de Rata Manía (puerto 8000 o el que uses con uvicorn)
API_BASE = os.getenv("CHATBOT_API_URL", "http://127.0.0.1:8011").rstrip("/")
CHAT_RUTAS = "/chat"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
ACCIONES = {"servicios", "disponibilidad", "crear", "modificar", "cancelar", "fuera_de_alcance"}
CONTROL_WORDS = {"confirmar", "abortar", "no", "cancelar solicitud", "/reset"}


INSTRUCCIONES = """
Eres un extractor de datos en formato JSON estricto para la tienda "Rata mania.". 

Tu ÚNICA función es analizar el mensaje del usuario y extraer la información en el siguiente JSON exacto:

{
  "intencion": "adoptar", 
  "servicio": "rata_dumbo",
  "fecha": "YYYY-MM-DD",
  "hora": "HH:MM",
  "cliente": "Nombre"
}

Reglas estrictas de "intencion":
- Usa "adoptar", "comprar" o "reservar" si el usuario quiere agendar una cita, adoptar o adquirir un producto/mascota.
- Usa "catalogo" si el usuario pregunta qué tienen disponible.
- Usa "fuera" ÚNICAMENTE si el mensaje no tiene ninguna relación con la tienda.

Reglas de extracción:
- "servicio": Si menciona una rata (dumbo, husky, hairless) o accesorio, extrae el identificador (ej: "rata_dumbo").
- "fecha": Extrae cualquier fecha expresada en formato AAAA-MM-DD.
- "hora": Extrae cualquier hora en formato HH:MM.
- "cliente": Extrae el nombre de la persona si lo indica (ej: "Carlos").

Mensaje a analizar:
"{input}"

Responde ÚNICAMENTE con el objeto JSON parseable. Sin bloques de código markdown extra si no son necesarios, sin explicaciones.



"""
#INSTRUCCIONES = """
#Eres el asistente virtual de Rata Manía. Analiza el mensaje del usuario y extrae los datos clave.
#Devuelve únicamente un objeto JSON estricto con estas claves:
#- accion: (servicios, disponibilidad, crear, modificar, cancelar, fuera_de_alcance)
#- cliente: nombre de la persona si lo menciona, si no, cadena vacía ""
#- servicio: variedad de rata o accesorio mencionado (ej. rata_dumbo), si no, cadena vacía ""
#- fecha: formato AAAA-MM-DD si se menciona, si no, cadena vacía ""
#- hora: formato HH:MM si se menciona, si no, cadena vacía ""
#- codigo: si aplica para modificar/cancelar, si no, cadena vacía ""
#No inventes datos que el usuario no haya escrito.
#"""


def peticion_json(url, metodo="GET", datos=None, headers=None):
    cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8") if datos is not None else None
    encabezados = {"Content-Type": "application/json"} if cuerpo is not None else {}
    encabezados.update(headers or {})
    solicitud = Request(url, data=cuerpo, headers=encabezados, method=metodo)
    with urlopen(solicitud, timeout=30) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def _es_control(pregunta):
    texto = (pregunta or "").strip()
    return texto.lower() in CONTROL_WORDS


def _heuristica_plan(pregunta):
    """Fallback local para seguir operando sin Groq o si el modelo/clave rechaza la llamada."""
    if _es_control(pregunta):
        return {"accion": "servicios", "cliente": "", "servicio": "", "fecha": "", "hora": "", "codigo": ""}
    texto = (pregunta or "").strip()
    lower = texto.lower()

    # 1) Nombres directos del cliente: "jhon", "bartolo fernandez", "a nombre de jhon"
    cliente = ""
    m = re.search(r"(?:a nombre de|me llamo|mi nombre es|soy)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ .'-]+)", texto, re.I)
    if m:
        cliente = m.group(1).strip()
    elif texto and not any(p in lower for p in ["hola", "buenas", "ayuda", "qué", "cuánto", "catalogo", "servicios", "reservar", "agendar", "comprar", "adoptar", "visita", "cita", "cancelar", "modificar", "horario", "ocupado", "libre", "cerrado"]) and re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ .'-]*", texto):
        cliente = texto.strip()

    # 2) Si el usuario está dando un nombre, no reiniciar el catálogo; seguir la reserva.
    if cliente:
        return {
            "accion": "crear",
            "cliente": cliente,
            "servicio": "",
            "fecha": "",
            "hora": "",
            "codigo": "",
        }

    # 3) Intención y extracción del resto
    accion = "servicios"
    if any(p in lower for p in ["cancelar", "anular", "borrar"]):
        accion = "cancelar"
    elif any(p in lower for p in ["modificar", "cambiar", "mover", "actualizar", "mejor a las"]):
        accion = "modificar"
    elif any(p in lower for p in ["disponibilidad", "horario", "ocupado", "libre", "cerrado"]):
        accion = "disponibilidad"
    elif any(p in lower for p in ["reservar", "agendar", "adoptar", "comprar", "visita", "cita"]):
        accion = "crear"
    elif any(p in lower for p in ["hola", "buenas", "ayuda", "qué", "cuánto", "catalogo", "servicios"]):
        accion = "servicios"
    elif any(p in lower for p in ["fuera", "aleatorio", "nada", "otro tema"]):
        accion = "fuera_de_alcance"

    # Si el mensaje solo trae una fecha o una hora, lo tratamos como continuación.
    if re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto) and not any(p in lower for p in ["hola", "catalogo", "servicios", "qué", "cuánto"]):
        accion = "crear"
    if re.search(r"\b\d{1,2}:\d{2}\b", texto) and not any(p in lower for p in ["hola", "catalogo", "servicios", "qué", "cuánto"]):
        accion = "crear"

    # Si el texto menciona un servicio o una visita con servicio, también es crear.
    servicios = [
        "rata_dumbo", "rata_husky", "rata_hairless",
        "jaula_equipada", "alimento_premium"
    ]
    servicio = ""
    for nombre in servicios:
        if nombre in lower:
            servicio = nombre
            break
    if servicio and ("quiero" in lower or "necesito" in lower or "visita" in lower or "reserva" in lower or "cita" in lower):
        accion = "crear"

    fecha = ""
    m = re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto)
    if m:
        fecha = m.group(0)

    hora = ""
    m = re.search(r"\b\d{1,2}:\d{2}\b", texto)
    if m:
        hora = m.group(0)

    codigo = ""
    m = re.search(r"\bPN-[A-Z0-9]+\b", texto, re.I)
    if m:
        codigo = m.group(0).upper()

    return {
        "accion": accion,
        "cliente": cliente,
        "servicio": servicio,
        "fecha": fecha,
        "hora": hora,
        "codigo": codigo,
    }


def _normalizar_plan(plan, pregunta):
    """Ajusta la intención entrante para reforzar el flujo de reserva."""
    if _es_control(pregunta):
        return {"accion": "servicios", "cliente": "", "servicio": "", "fecha": "", "hora": "", "codigo": ""}
    if not isinstance(plan, dict):
        return {"accion": "servicios", "cliente": "", "servicio": "", "fecha": "", "hora": "", "codigo": ""}

    accion = str(plan.get("accion") or plan.get("intencion") or "").strip().lower()
    texto = (pregunta or "").strip()
    lower = texto.lower()

    nombre_patron = re.search(r"(?:a nombre de|me llamo|mi nombre es|soy)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ .'-]+)", texto, re.I)
    nombre_suelto = False
    if not nombre_patron and texto and re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ .'-]*", texto):
        nombre_suelto = True

    if accion in {"adoptar", "comprar", "reservar", "reserva", "agendar", "cita", "visita", "compra", "crear"}:
        accion = "crear"
    elif accion in {"consultar", "consulta"}:
        accion = "servicios"
    elif accion in {"catalogo", "catalog", "ver", "producto", "mascota", "informacion", "listar_servicios", "consultar_servicios"}:
        accion = "servicios"
    elif accion in {"fuera", "fuera_de_alcance", "no_relacionado"}:
        accion = "fuera_de_alcance"

    if accion == "servicios":
        if nombre_patron or nombre_suelto:
            accion = "crear"
        elif re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto) or re.search(r"\b\d{1,2}:\d{2}\b", texto):
            accion = "crear"
        elif "visita" in lower or "reservar" in lower or "agendar" in lower or "adoptar" in lower or "comprar" in lower:
            accion = "crear"
        elif any(nombre in lower for nombre in ["rata_dumbo", "rata_husky", "rata_hairless", "jaula_equipada", "alimento_premium"]):
            accion = "crear"

    cliente = str(plan.get("cliente") or "").strip()
    if cliente.lower() in {"confirmar", "abortar", "no"}:
        cliente = ""
    if not cliente and nombre_patron:
        cliente = nombre_patron.group(1).strip()
    if not cliente and nombre_suelto:
        cliente = texto.strip()

    servicio = str(plan.get("servicio") or "").strip()
    if not servicio:
        for nombre in ["rata_dumbo", "rata_husky", "rata_hairless", "jaula_equipada", "alimento_premium"]:
            if nombre in lower:
                servicio = nombre
                break

    fecha = str(plan.get("fecha") or "").strip()
    if not fecha:
        m = re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto)
        if m:
            fecha = m.group(0)

    hora = str(plan.get("hora") or "").strip()
    if not hora:
        m = re.search(r"\b\d{1,2}:\d{2}\b", texto)
        if m:
            hora = m.group(0)

    codigo = str(plan.get("codigo") or "").strip()
    if not codigo:
        m = re.search(r"\bPN-[A-Z0-9]+\b", texto, re.I)
        if m:
            codigo = m.group(0).upper()

    return {
        "accion": accion or "servicios",
        "cliente": cliente,
        "servicio": servicio,
        "fecha": fecha,
        "hora": hora,
        "codigo": codigo,
    }


def interpretar(pregunta, clave, modelo):
    if not clave or not modelo:
        return _heuristica_plan(pregunta)

    try:
        payload = {
            "model": modelo,
            "messages": [
                {"role": "system", "content": INSTRUCCIONES},
                {"role": "user", "content": pregunta},
            ],
            "stream": False,
        }
        respuesta = peticion_json(
            GROQ_URL, "POST", payload,
            {"Authorization": f"Bearer {clave}"},
        )
        texto = respuesta["choices"][0]["message"]["content"]

        texto_limpio = texto.strip()
        if texto_limpio.startswith("```json"):
            texto_limpio = texto_limpio[7:]
        if texto_limpio.endswith("```"):
            texto_limpio = texto_limpio[:-3]

        plan = json.loads(texto_limpio.strip())
        plan = _normalizar_plan(plan, pregunta)
        if not isinstance(plan, dict) or plan.get("accion") not in ACCIONES:
            raise ValueError("Groq no devolvió una acción válida")

        return {campo: str(plan.get(campo) or "").strip()
                for campo in ("accion", "cliente", "servicio", "fecha", "hora", "codigo")}

    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError):
        return _heuristica_plan(pregunta)


def ejecutar(plan, pregunta_original, session_id, api_base=API_BASE):
    """Envía la intención interpretada y el mensaje original al endpoint /chat de la FastAPI."""
    url = api_base + CHAT_RUTAS
    pregunta = (pregunta_original or "").strip()

    if _es_control(pregunta):
        cuerpo_peticion = {
            "session_id": session_id,
            "mensaje": pregunta,
            "datos": {}
        }
        respuesta_fastapi = peticion_json(url, "POST", cuerpo_peticion)
        return respuesta_fastapi

    # Filtramos valores del plan que puedan ser palabras de control o vacíos.
    plan = dict(plan or {})
    if str(plan.get("cliente", "")).strip().lower() in {"confirmar", "abortar", "no"}:
        plan["cliente"] = ""
    if str(plan.get("accion", "")).strip().lower() in {"confirmar", "abortar", "no"}:
        plan["accion"] = "servicios"

    datos_payload = {
        "intencion": plan.get("accion"),
        "cliente": plan.get("cliente"),
        "servicio": plan.get("servicio"),
        "fecha": plan.get("fecha"),
        "hora": plan.get("hora"),
        "codigo": plan.get("codigo")
    }
    datos_payload = {k: v for k, v in datos_payload.items() if v}

    cuerpo_peticion = {
        "session_id": session_id,
        "mensaje": pregunta,
        "datos": datos_payload
    }

    respuesta_fastapi = peticion_json(url, "POST", cuerpo_peticion)
    return respuesta_fastapi


def _leer_error_http(error):
    """Devuelve un texto legible a partir de un HTTPError de Groq o de la FastAPI."""
    detalle = ""
    try:
        cuerpo = error.read().decode("utf-8", errors="replace")
        if cuerpo:
            detalle = f" | {cuerpo[:300]}"
    except Exception:
        detalle = ""
    return f"HTTP {error.code}{detalle}"


def _mensaje_http_409(plan, error):
    """Explica el conflicto de disponibilidad a quien intenta confirmar una reserva."""
    servicio = str(plan.get("servicio") or "").strip() or "el servicio solicitado"
    fecha = str(plan.get("fecha") or "").strip() or "la fecha elegida"
    hora = str(plan.get("hora") or "").strip() or "esa hora"
    detalle = _leer_error_http(error)
    if "ocupado" in detalle.lower() or "fuera de rango" in detalle.lower() or "disponibilidad" in detalle.lower():
        return (
            f"Ese horario no está disponible: {servicio} en {fecha} a las {hora}. "
            "Elige otra hora o fecha libre y vuelve a confirmar."
        )
    return f"Eso no se puede confirmar porque el horario ya no está disponible. Elige otra fecha u hora libre. Detalle: {detalle}"


def main():
    clave = os.getenv("GROQ_API_KEY", "").strip() or getpass("API key de Groq: ").strip()
    modelo = os.getenv("GROQ_MODEL", "").strip() or input("ID del modelo de Groq (ej. llama3-70b-8192): ").strip()
    if not clave or not modelo:
        print("No hay clave/modelo válido de Groq. Se usará el modo local de respaldo para probar la API.")

    session_id = "terminal_user_1"
    print("\n¡Bienvenido a Rata Manía! Escribe una solicitud. Para terminar, escribe SALIR.")

    ultimo_plan = {}
    while True:
        pregunta = input("\nTú: ").strip()
        if pregunta.casefold() == "salir":
            break
        if not pregunta:
            continue
        try:
            plan = interpretar(pregunta, clave, modelo)
            ultimo_plan = plan
            resultado = ejecutar(plan, pregunta, session_id)
            print(f"Chatbot: {resultado.get('respuesta', resultado)}")

        except HTTPError as error:
            if error.code == 409:
                print(f"Chatbot: {_mensaje_http_409(ultimo_plan or {}, error)}")
            else:
                print(f"Error de Groq o API: HTTP {error.code}. Revisa la clave/modelo y que uvicorn main:app --host 0.0.0.0 --port 8011 --reload esté corriendo.")
        except (URLError, TimeoutError) as e:
            print(f"No pude conectar con Groq o con la FastAPI. Asegúrate de que uvicorn main:app --host 0.0.0.0 --port 8011 --reload esté corriendo. Detalle: {e}")
        except (ValueError, KeyError, IndexError, TypeError) as e:
            print(f"No pude interpretar la respuesta. Detalle: {e}")


if __name__ == "__main__":
    main()