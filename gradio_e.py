import os
import re
import json
import gradio as gr
from getpass import getpass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_BASE = os.getenv("CHATBOT_API_URL", "http://127.0.0.1:8011").rstrip("/")
CHAT_RUTAS = "/chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CLAVE = os.getenv("GROQ_API_KEY", "").strip()
MODELO = os.getenv("GROQ_MODEL", "").strip()

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
    if _es_control(pregunta):
        return {"accion": "servicios", "cliente": "", "servicio": "", "fecha": "", "hora": "", "codigo": ""}
    texto = (pregunta or "").strip()
    lower = texto.lower()

    cliente = ""
    m = re.search(r"(?:a nombre de|me llamo|mi nombre es|soy)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ .'-]+)", texto, re.I)
    if m:
        cliente = m.group(1).strip()
    elif texto and not any(p in lower for p in ["hola", "buenas", "ayuda", "qué", "cuánto", "catalogo", "servicios", "reservar", "agendar", "comprar", "adoptar", "visita", "cita", "cancelar", "modificar", "horario", "ocupado", "libre", "cerrado"]) and re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ .'-]*", texto):
        cliente = texto.strip()

    if cliente:
        return {"accion": "crear", "cliente": cliente, "servicio": "", "fecha": "", "hora": "", "codigo": ""}

    accion = "servicios"
    if any(p in lower for p in ["cancelar", "anular", "borrar"]): accion = "cancelar"
    elif any(p in lower for p in ["modificar", "cambiar", "mover", "actualizar", "mejor a las"]): accion = "modificar"
    elif any(p in lower for p in ["disponibilidad", "horario", "ocupado", "libre", "cerrado"]): accion = "disponibilidad"
    elif any(p in lower for p in ["reservar", "agendar", "adoptar", "comprar", "visita", "cita"]): accion = "crear"
    elif any(p in lower for p in ["hola", "buenas", "ayuda", "qué", "cuánto", "catalogo", "servicios"]): accion = "servicios"
    elif any(p in lower for p in ["fuera", "aleatorio", "nada", "otro tema"]): accion = "fuera_de_alcance"

    if re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto) and not any(p in lower for p in ["hola", "catalogo", "servicios"]): accion = "crear"
    if re.search(r"\b\d{1,2}:\d{2}\b", texto) and not any(p in lower for p in ["hola", "catalogo", "servicios"]): accion = "crear"

    servicios = ["rata_dumbo", "rata_husky", "rata_hairless", "jaula_equipada", "alimento_premium"]
    servicio = next((s for s in servicios if s in lower), "")
    if servicio and any(p in lower for p in ["quiero", "necesito", "visita", "reserva", "cita"]): accion = "crear"

    fecha = re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto)
    fecha = fecha.group(0) if fecha else ""
    hora = re.search(r"\b\d{1,2}:\d{2}\b", texto)
    hora = hora.group(0) if hora else ""
    codigo = re.search(r"\bPN-[A-Z0-9]+\b", texto, re.I)
    codigo = codigo.group(0).upper() if codigo else ""

    return {"accion": accion, "cliente": cliente, "servicio": servicio, "fecha": fecha, "hora": hora, "codigo": codigo}

def _normalizar_plan(plan, pregunta):
    if _es_control(pregunta) or not isinstance(plan, dict):
        return {"accion": "servicios", "cliente": "", "servicio": "", "fecha": "", "hora": "", "codigo": ""}

    accion = str(plan.get("accion") or plan.get("intencion") or "").strip().lower()
    texto = (pregunta or "").strip()
    lower = texto.lower()

    nombre_patron = re.search(r"(?:a nombre de|me llamo|mi nombre es|soy)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ .'-]+)", texto, re.I)
    nombre_suelto = not nombre_patron and texto and re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúñÑ][A-Za-zÁÉÍÓÚáéíóúñÑ .'-]*", texto)

    if accion in {"adoptar", "comprar", "reservar", "reserva", "agendar", "cita", "visita", "compra", "crear"}: accion = "crear"
    elif accion in {"consultar", "consulta", "catalogo", "catalog", "ver", "producto", "mascota", "informacion", "listar_servicios", "consultar_servicios"}: accion = "servicios"
    elif accion in {"fuera", "fuera_de_alcance", "no_relacionado"}: accion = "fuera_de_alcance"

    if accion == "servicios":
        if nombre_patron or nombre_suelto or re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto) or re.search(r"\b\d{1,2}:\d{2}\b", texto) or any(p in lower for p in ["visita", "reservar", "agendar", "adoptar", "comprar"]):
            accion = "crear"
        elif any(nombre in lower for nombre in ["rata_dumbo", "rata_husky", "rata_hairless", "jaula_equipada", "alimento_premium"]):
            accion = "crear"

    cliente = str(plan.get("cliente") or "").strip()
    if cliente.lower() in {"confirmar", "abortar", "no"}: cliente = ""
    if not cliente and nombre_patron: cliente = nombre_patron.group(1).strip()
    if not cliente and nombre_suelto: cliente = texto.strip()

    servicio = str(plan.get("servicio") or "").strip()
    if not servicio:
        servicio = next((s for s in ["rata_dumbo", "rata_husky", "rata_hairless", "jaula_equipada", "alimento_premium"] if s in lower), "")

    fecha = str(plan.get("fecha") or "").strip()
    if not fecha:
        f = re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto)
        fecha = f.group(0) if f else ""

    hora = str(plan.get("hora") or "").strip()
    if not hora:
        h = re.search(r"\b\d{1,2}:\d{2}\b", texto)
        hora = h.group(0) if h else ""

    codigo = str(plan.get("codigo") or "").strip()
    if not codigo:
        c = re.search(r"\bPN-[A-Z0-9]+\b", texto, re.I)
        codigo = c.group(0).upper() if c else ""

    return {"accion": accion or "servicios", "cliente": cliente, "servicio": servicio, "fecha": fecha, "hora": hora, "codigo": codigo}

def interpretar(pregunta, clave, modelo):
    if not clave or not modelo:
        return _heuristica_plan(pregunta)

    try:
        payload = {
            "model": modelo,
            "messages": [{"role": "system", "content": INSTRUCCIONES}, {"role": "user", "content": pregunta}],
            "stream": False,
        }
        respuesta = peticion_json(GROQ_URL, "POST", payload, {"Authorization": f"Bearer {clave}"})
        texto = respuesta["choices"][0]["message"]["content"].strip()
        
        if texto.startswith("```json"): texto = texto[7:]
        if texto.startswith("```"): texto = texto[3:]
        if texto.endswith("```"): texto = texto[:-3]

        plan = _normalizar_plan(json.loads(texto.strip()), pregunta)
        if not isinstance(plan, dict) or plan.get("accion") not in ACCIONES:
            raise ValueError("Groq no devolvió una acción válida")

        return {campo: str(plan.get(campo) or "").strip() for campo in ("accion", "cliente", "servicio", "fecha", "hora", "codigo")}
    except Exception:
        return _heuristica_plan(pregunta)

def ejecutar(plan, pregunta_original, session_id):
    url = API_BASE + CHAT_RUTAS
    pregunta = (pregunta_original or "").strip()

    if _es_control(pregunta):
        return peticion_json(url, "POST", {"session_id": session_id, "mensaje": pregunta, "datos": {}})

    plan = dict(plan or {})
    if str(plan.get("cliente", "")).strip().lower() in {"confirmar", "abortar", "no"}: plan["cliente"] = ""
    if str(plan.get("accion", "")).strip().lower() in {"confirmar", "abortar", "no"}: plan["accion"] = "servicios"

    datos_payload = {k: v for k, v in {
        "intencion": plan.get("accion"), "cliente": plan.get("cliente"),
        "servicio": plan.get("servicio"), "fecha": plan.get("fecha"),
        "hora": plan.get("hora"), "codigo": plan.get("codigo")
    }.items() if v}

    return peticion_json(url, "POST", {"session_id": session_id, "mensaje": pregunta, "datos": datos_payload})


def responder_usuario(mensaje, historial):
    if not mensaje.strip():
        return "Por favor, escribe una consulta."

    try:
        session_id = "gradio_user_1"
        plan = interpretar(mensaje, CLAVE, MODELO)
        
        try:
            resultado = ejecutar(plan, mensaje, session_id)
            return resultado.get("respuesta", str(resultado))
            
        except HTTPError as error:
            # Manejo de conflictos de horario o errores devueltos por tu main.py (FastAPI)
            if error.code == 409:
                return "Ese horario no está disponible. Elige otra hora o fecha libre y vuelve a confirmar."
            return f"Error de la API: HTTP {error.code}. Asegúrate de que FastAPI esté corriendo en {API_BASE}."
            
        except (URLError, TimeoutError):
            return f"No pude conectar con FastAPI. Asegúrate de que esté ejecutándose en {API_BASE}."

    except Exception as e:
        return f"Ocurrió un error general: {str(e)}"


demo = gr.ChatInterface(
    fn=responder_usuario,
    title="Ratas mania",
    description="Habla con nuestro ratasistente :)",
    textbox=gr.Textbox(
        placeholder="Escribe qué quieres reservar...",
        container=False,
        scale=7,
    ),
)

if __name__ == "__main__":
    if not CLAVE or not MODELO:
        print("[AVISO] No configuraste GROQ_API_KEY o GROQ_MODEL en la consola. Se usará el modo heurístico.")
    else:
        print(f"[OK] Modelo conectado: {MODELO}")
        
    demo.launch(server_name="0.0.0.0", server_port=7860)
