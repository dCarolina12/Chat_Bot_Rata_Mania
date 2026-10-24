
import json
import os
import re
import threading
import uuid
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
import subprocess
# Configuracion global

app = FastAPI(title="Rata mania · API de Reservas")
ARCHIVO = "reservas.json"
NEGOCIO_FILE = "negocio.json"
_lock = threading.Lock()
ZONA = ZoneInfo("America/Bogota")
SESIONES: Dict[str, Dict[str, Any]] = {}

script_ = Path(__file__).resolve().parent / "scripts/ratadb.sh"


def _cargar_negocio() -> dict:
    if not os.path.exists(NEGOCIO_FILE):
        return {}
    try:
        with open(NEGOCIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _cargar_reservas() -> list:
    if not os.path.exists(ARCHIVO):
        return []
    try:
        with open(str(ARCHIVO), "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("reservas.json no contiene una lista")
        return data
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Error al leer reservas: {exc}")


def _guardar_reservas(reservas: list) -> None:
    archivo_str = str(ARCHIVO)
    tmp = archivo_str + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reservas, f, ensure_ascii=False, indent=2)
        os.replace(tmp, archivo_str)     
        subprocess.run(["bash", str(script_)], check=True, capture_output=True)

    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"Error al guardar reservas: {exc}")

def _guardar_reservas_cancelar(reservas: list, codigo: str) -> None:
    archivo_str = str(ARCHIVO)
    tmp = archivo_str + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reservas, f, ensure_ascii=False, indent=2)
        os.replace(tmp, archivo_str)
        subprocess.run(["bash", str(script_), codigo], check=True, capture_output=True)

    except OSError as e:
        raise HTTPException(status_code=503, detail=f"Error al cancelar reservas: {e}")

#disponibilidad

def horarios_libres(dia: date, servicio: str, reservas: list) -> List[str]:
    """Devuelve los horarios disponibles para un día y servicio dados."""
    negocio = _cargar_negocio()
    horarios_cfg = negocio.get("horarios", {})
    paso = int(negocio.get("paso_minutos", 30))
    servicios = negocio.get("servicios", {})

    if servicio not in servicios:
        return []

    duracion_str = servicios[servicio].get("duracion", "entrega")
    try:
        duracion_min = int(duracion_str)
    except (ValueError, TypeError):
        duracion_min = paso

    dia_semana = str(dia.weekday())  # 0=lunes … 6=domingo
    if dia_semana not in horarios_cfg:
        return []

    apertura_str, cierre_str = horarios_cfg[dia_semana]
    apertura = datetime.strptime(apertura_str, "%H:%M")
    cierre = datetime.strptime(cierre_str, "%H:%M")

    slots = []
    cursor = apertura
    while cursor + timedelta(minutes=duracion_min) <= cierre:
        slots.append(cursor.strftime("%H:%M"))
        cursor += timedelta(minutes=paso)

    ocupados = [
        r for r in reservas
        if r.get("fecha") == dia.isoformat() and r.get("estado") == "activa"
    ]

    libres = []
    for slot in slots:
        slot_dt = datetime.strptime(slot, "%H:%M")
        slot_fin = slot_dt + timedelta(minutes=duracion_min)
        colisiona = False
        for res in ocupados:
            res_inicio = datetime.strptime(res["hora"], "%H:%M")
            res_dur_str = servicios.get(res.get("item", ""), {}).get("duracion", str(paso))
            try:
                res_dur = int(res_dur_str)
            except (ValueError, TypeError):
                res_dur = paso
            res_fin = res_inicio + timedelta(minutes=res_dur)
            if slot_dt < res_fin and slot_fin > res_inicio:
                colisiona = True
                break
        if not colisiona:
            libres.append(slot)

    return libres


def _validar_horario(dia: date, servicio: str, hora: str, reservas: list) -> None:
    """Lanza 409/422 si el horario no está disponible."""
    try:
        datetime.strptime(hora, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato de hora inválido (HH:MM).")

    hoy = datetime.now(ZONA).date()
    if dia <= hoy:
        raise HTTPException(status_code=422, detail="La fecha debe ser futura.")

    libres = horarios_libres(dia, servicio, reservas)
    if not libres:
        raise HTTPException(status_code=409, detail="Sin disponibilidad para ese día o servicio.")
    if hora not in libres:
        raise HTTPException(status_code=409, detail=f"Horario ocupado o fuera de rango. Disponibles: {libres}")


class ReservaIn(BaseModel):
    cliente: str
    servicio: str
    fecha: str          # AAAA-MM-DD
    hora: str           # HH:MM
    confirmado: bool

    @field_validator("confirmado")
    @classmethod
    def debe_confirmar(cls, v):
        if not v:
            raise ValueError("Debes enviar confirmado=true para crear la reserva.")
        return v

    @field_validator("fecha")
    @classmethod
    def fecha_futura(cls, v):
        try:
            d = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Formato de fecha inválido (AAAA-MM-DD).")
        zona = ZoneInfo("America/Bogota")
        if d <= datetime.now(zona).date():
            raise ValueError("La fecha debe ser futura.")
        return v

    @field_validator("hora")
    @classmethod
    def hora_valida(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Formato de hora inválido (HH:MM).")
        return v


class ReservaUpdate(BaseModel):
    cliente: Optional[str] = None
    fecha: Optional[str] = None
    hora: Optional[str] = None

    @field_validator("fecha")
    @classmethod
    def fecha_futura(cls, v):
        if v is None:
            return v
        try:
            d = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Formato de fecha inválido (AAAA-MM-DD).")
        zona = ZoneInfo("America/Bogota")
        if d <= datetime.now(zona).date():
            raise ValueError("La fecha debe ser futura.")
        return v


class ChatInput(BaseModel):
    session_id: str
    mensaje: str
    datos: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("datos")
    @classmethod
    def sin_confirmado_externo(cls, v):
        if v and "confirmado" in v:
            raise ValueError("El campo 'confirmado' no puede enviarse dentro de 'datos'.")
        return v


@app.post("/reservas", status_code=201)
async def reservar(payload: ReservaIn):
    """Crea una reserva nueva si el horario está disponible."""
    negocio = _cargar_negocio()
    servicios = negocio.get("servicios", {})

    if payload.servicio not in servicios:
        raise HTTPException(
            status_code=422,
            detail=f"Servicio no reconocido. Disponibles: {list(servicios.keys())}"
        )

    dia = date.fromisoformat(payload.fecha)

    with _lock:
        reservas = _cargar_reservas()
        _validar_horario(dia, payload.servicio, payload.hora, reservas)

        info_servicio = servicios[payload.servicio]
        nueva = {
            "codigo": "PN-" + uuid.uuid4().hex[:8].upper(),
            "cliente": payload.cliente,
            "item": payload.servicio,
            "fecha": payload.fecha,
            "hora": payload.hora,
            "precio_cop": info_servicio.get("precio", 0),
            "duracion_minutos": info_servicio.get("duracion", "entrega"),
            "estado": "activa",
            "creada_en": datetime.now(ZONA).isoformat(),
            "cancelada_en": None,
        }
        reservas.append(nueva)
        _guardar_reservas(reservas)

    return nueva


@app.get("/reservas/{codigo}")
async def consultar_reserva(codigo: str):
    """Devuelve la reserva indicada por su código único."""
    reservas = _cargar_reservas()
    for r in reservas:
        if r.get("codigo") == codigo:
            return r
    raise HTTPException(status_code=404, detail=f"Reserva '{codigo}' no encontrada.")


@app.delete("/reservas/{codigo}")
async def cancelar_reserva(codigo: str, confirmado: bool = Query(False)):
    """Marca la reserva como cancelada (no la elimina del archivo)."""
    if not confirmado:
        raise HTTPException(
            status_code=422,
            detail="Confirma con ?confirmado=true para cancelar la reserva."
        )

    with _lock:
        reservas = _cargar_reservas()
        for r in reservas:
            if r.get("codigo") == codigo:
                if r["estado"] == "cancelada":
                    return r   # Idempotente: ya estaba cancelada
                r["estado"] = "cancelada"
                r["cancelada_en"] = datetime.now(ZONA).isoformat()
                _guardar_reservas(reservas)
                return r
    raise HTTPException(status_code=404, detail=f"Reserva '{codigo}' no encontrada.")


@app.put("/reservas/{codigo}")
async def actualizar_reserva(codigo: str, cambios: ReservaUpdate):
    """Actualiza cliente, fecha u hora de una reserva activa."""
    with _lock:
        reservas = _cargar_reservas()
        for r in reservas:
            if r.get("codigo") == codigo:
                if r["estado"] != "activa":
                    raise HTTPException(
                        status_code=409,
                        detail="Solo se pueden actualizar reservas activas."
                    )
                nueva_fecha = cambios.fecha or r["fecha"]
                nueva_hora = cambios.hora or r["hora"]
                servicio = r["item"]
                dia = date.fromisoformat(nueva_fecha)

                otras = [x for x in reservas if x.get("codigo") != codigo]
                _validar_horario(dia, servicio, nueva_hora, otras)

                if cambios.cliente:
                    r["cliente"] = cambios.cliente
                r["fecha"] = nueva_fecha
                r["hora"] = nueva_hora
                _guardar_reservas(reservas)
                return r

    raise HTTPException(status_code=404, detail=f"Reserva '{codigo}' no encontrada.")


@app.get("/servicios")
async def listar_servicios():
    """Devuelve el catálogo completo del negocio."""
    negocio = _cargar_negocio()
    return {
        "nombre": negocio.get("nombre", "Rata mania"),
        "horarios": negocio.get("horarios", {}),
        "servicios": negocio.get("servicios", {}),
        "condiciones": negocio.get("condiciones", ""),
    }


@app.get("/disponibilidad")
async def disponibilidad(
    fecha: str = Query(..., description="AAAA-MM-DD"),
    servicio: str = Query(..., description="Nombre del servicio"),
):
    """Lista os horarios libres para la fecha y servicio indicados."""
    try:
        dia = date.fromisoformat(fecha)
    except ValueError:
        raise HTTPException(status_code=422, detail="Fecha inválida (AAAA-MM-DD).")

    negocio = _cargar_negocio()
    if servicio not in negocio.get("servicios", {}):
        raise HTTPException(
            status_code=422,
            detail=f"Servicio no reconocido. Disponibles: {list(negocio['servicios'].keys())}"
        )

    reservas = _cargar_reservas()
    libres = horarios_libres(dia, servicio, reservas)
    return {"fecha": fecha, "servicio": servicio, "horarios": libres}


@app.post("/chat")
async def chat_endpoint(payload: ChatInput):
    """
    Flujo de lenguaje natural mediado por Flowise/Groq.

    El LLM extrae intención y datos; este endpoint mantiene el estado de la
    sesión y ejecuta las operaciones CRUD cuando corresponde.

    Intenciones reconocidas:
      - reservar / adoptar / compra / cita / visita
      - consultar / informacion / catalogo / ver / producto / mascota
      - cancelar
      - actualizar / continuar (para corregir datos del resumen pendiente)

    Controles especiales en el mensaje:
      - CONFIRMAR  → ejecuta la acción pendiente
      - ABORTAR / NO → descarta estado
      - /reset     → limpia sesión sin tocar reservas
    """
    sid = payload.session_id
    datos = payload.datos or {}
    mensaje = payload.mensaje.strip()
    mensaje_lower = mensaje.lower()

    print(f"\n[DEBUG] Session={sid} | Mensaje='{mensaje}' | Datos={datos}")

    # Inicializar sesión si no existe
    if sid not in SESIONES:
        SESIONES[sid] = {}

    sesion = SESIONES[sid]
    intencion = str((datos.get("intencion") or datos.get("accion") or "")).strip().lower()
    if not intencion and "servicios" in mensaje_lower:
        intencion = "servicios"

    if (
        not sesion.get("cliente")
        and sesion.get("servicio")
        and sesion.get("fecha")
        and sesion.get("hora")
        and mensaje
        and not mensaje_lower.startswith(("hola", "ayuda", "catalogo", "servicios", "qué", "cuanto", "cuánto", "ver", "producto", "mascota"))
    ):
        sesion["cliente"] = _normalizar_cliente(mensaje)
        intencion = "crear"

    if intencion in {"servicios", "catalogo", "ver", "producto", "mascota", "informacion", "consulta", "consultar_servicios", "listar_servicios"} and (
        sesion.get("servicio") or sesion.get("fecha") or sesion.get("hora") or sesion.get("cliente")
    ):
        intencion = "crear"

    if mensaje_lower == "/reset":
        SESIONES.pop(sid, None)
        return {"respuesta": "Sesión reiniciada.", "estado_sesion": {}}

    if mensaje_lower in ("abortar", "no", "cancelar solicitud"):
        SESIONES.pop(sid, None)
        return {
            "respuesta": "De acuerdo, descarté la solicitud. ¿En qué más te puedo ayudar?",
            "estado_sesion": {},
        }

    if mensaje_lower == "confirmar":
        pendiente = sesion.get("pendiente")
        if not pendiente:
            return {
                "respuesta": "No hay un resumen pendiente por confirmar. Indícame qué deseas hacer.",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }

        accion = pendiente["accion"]

        # Confirmar RESERVA
        if accion == "reservar":
            d = pendiente["datos"]
            negocio = _cargar_negocio()
            servicios = negocio.get("servicios", {})
            servicio = d.get("servicio", "")
            if servicio not in servicios:
                sesion.pop("pendiente", None)
                return {"respuesta": f"Servicio '{servicio}' no válido.", "estado_sesion": sesion}

            dia = date.fromisoformat(d["fecha"])
            with _lock:
                reservas = _cargar_reservas()
                try:
                    _validar_horario(dia, servicio, d["hora"], reservas)
                except HTTPException as exc:
                    sesion.pop("pendiente", None)
                    raise exc

                info = servicios[servicio]
                nueva = {
                    "codigo": "PN-" + uuid.uuid4().hex[:8].upper(),
                    "cliente": d["cliente"],
                    "item": servicio,
                    "fecha": d["fecha"],
                    "hora": d["hora"],
                    "precio_cop": info.get("precio", 0),
                    "duracion_minutos": info.get("duracion", "entrega"),
                    "estado": "activa",
                    "creada_en": datetime.now(ZONA).isoformat(),
                    "cancelada_en": None,
                }
                reservas.append(nueva)
                _guardar_reservas(reservas)

            sesion.pop("pendiente", None)
            sesion["ultimo_codigo"] = nueva["codigo"]
            return {
                "respuesta": (
                    f"Reserva registrada. Código: {nueva['codigo']}. "
                    f"{nueva['cliente']} tiene agendado {nueva['item']} "
                    f"el {nueva['fecha']} a las {nueva['hora']}."
                ),
                "estado_sesion": {k: v for k, v in sesion.items()},
            }

        # Confirmar CANCELACION
        if accion == "cancelar":
            codigo = pendiente["datos"]["codigo"]
            with _lock:
                reservas = _cargar_reservas()
                for r in reservas:
                    if r.get("codigo") == codigo:
                        r["estado"] = "cancelada"
                        r["cancelada_en"] = datetime.now(ZONA).isoformat()
                        _guardar_reservas_cancelar(reservas, codigo)
                        sesion.pop("pendiente", None)
                        return {
                            "respuesta": f"Reserva cancelada. ({codigo})",
                            "estado_sesion": {k: v for k, v in sesion.items()},
                        }
            sesion.pop("pendiente", None)
            raise HTTPException(status_code=404, detail=f"Reserva '{codigo}' no encontrada.")

    if intencion in {"continuar", "modificar", "actualizar"} and sesion.get("pendiente"):
        pendiente = sesion["pendiente"]
        for campo in ("cliente", "fecha", "hora", "servicio", "codigo"):
            if datos.get(campo):
                pendiente["datos"][campo] = datos[campo]
        return {
            "respuesta": _resumen_pendiente(pendiente),
            "estado_sesion": {k: v for k, v in sesion.items()},
        }

    for k, v in datos.items():
        if v and k != "intencion" and k != "accion":
            sesion[k] = v

    if intencion in {"servicios", "catalogo", "ver", "producto", "mascota", "informacion", "consultar_servicios", "listar_servicios"}:
        negocio = _cargar_negocio()
        servicios = negocio.get("servicios", {})
        items = ", ".join(servicios.keys()) if servicios else "sin datos"
        return {
            "respuesta": (
                f"En Rata mania tenemos: {items}. "
                "¿Cuál te interesa o deseas agendar una visita?"
            ),
            "estado_sesion": {k: v for k, v in sesion.items()},
        }

    if intencion == "disponibilidad":
        fecha = datos.get("fecha") or sesion.get("fecha")
        servicio = datos.get("servicio") or sesion.get("servicio")
        if not fecha or not servicio:
            return {
                "respuesta": "Para consultar disponibilidad necesito la fecha y el servicio.",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }
        try:
            dia = date.fromisoformat(fecha)
        except ValueError:
            raise HTTPException(status_code=422, detail="Fecha inválida (AAAA-MM-DD).")
        negocio = _cargar_negocio()
        if servicio not in negocio.get("servicios", {}):
            raise HTTPException(status_code=422, detail=f"Servicio no reconocido: {servicio}")
        libres = horarios_libres(dia, servicio, _cargar_reservas())
        return {
            "respuesta": f"Disponibilidad para {servicio} el {fecha}: {', '.join(libres) if libres else 'sin disponibilidad'}.",
            "estado_sesion": {k: v for k, v in sesion.items()},
        }

    if "consultar" in intencion or intencion == "consulta":
        codigo = datos.get("codigo") or sesion.get("codigo")
        if not codigo:
            return {
                "respuesta": "¿Cuál es el código de la reserva que deseas consultar?",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }
        reservas = _cargar_reservas()
        for r in reservas:
            if r.get("codigo") == codigo:
                return {
                    "respuesta": (
                        f"Reserva {r['codigo']}: {r['cliente']} — {r['item']} "
                        f"el {r['fecha']} a las {r['hora']}. Estado: {r['estado']}."
                    ),
                    "estado_sesion": {k: v for k, v in sesion.items()},
                }
        raise HTTPException(status_code=404, detail=f"Reserva '{codigo}' no encontrada.")

    if "cancelar" in intencion:
        codigo = datos.get("codigo") or sesion.get("codigo")
        if not codigo:
            return {
                "respuesta": "¿Cuál es el código de la reserva que deseas cancelar?",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }
        reservas = _cargar_reservas()
        reserva = next((r for r in reservas if r.get("codigo") == codigo), None)
        if not reserva:
            raise HTTPException(status_code=404, detail=f"Reserva '{codigo}' no encontrada.")

        pendiente = {"accion": "cancelar", "datos": {"codigo": codigo}}
        sesion["pendiente"] = pendiente
        return {
            "respuesta": (
                f"Vas a cancelar la reserva {codigo} "
                f"({reserva['cliente']} — {reserva['item']} el {reserva['fecha']} a las {reserva['hora']}). "
                "Responde CONFIRMAR para proceder o ABORTAR para cancelar."
            ),
            "estado_sesion": {k: v for k, v in sesion.items()},
        }

    es_reserva = any(p in intencion for p in ["adopt", "compra", "reserva", "cita", "visita", "reservar", "crear", "agendar"])
    tiene_datos = bool(sesion.get("servicio") or sesion.get("fecha"))

    if es_reserva or tiene_datos:
        negocio = _cargar_negocio()
        servicios = negocio.get("servicios", {})

        if not sesion.get("servicio"):
            items = ", ".join(servicios.keys())
            return {
                "respuesta": f"¿Qué producto o adopción te interesa? Opciones: {items}.",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }
        if sesion["servicio"] not in servicios:
            sesion.pop("servicio", None)
            return {
                "respuesta": "Ese servicio no está disponible. ¿Cuál eliges?",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }
        if not sesion.get("fecha"):
            return {
                "respuesta": "¿Para qué fecha (AAAA-MM-DD) deseas agendar tu visita?",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }
        if not sesion.get("hora"):
            dia = date.fromisoformat(sesion["fecha"])
            libres = horarios_libres(dia, sesion["servicio"], _cargar_reservas())
            horarios_txt = ", ".join(libres) if libres else "sin disponibilidad"
            return {
                "respuesta": f"Horarios disponibles para el {sesion['fecha']}: {horarios_txt}. ¿A qué hora prefieres?",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }
        if not sesion.get("cliente"):
            return {
                "respuesta": "¿A nombre de quién hacemos el registro?",
                "estado_sesion": {k: v for k, v in sesion.items()},
            }

        if not sesion.get("pendiente"):
            pendiente = {
                "accion": "reservar",
                "datos": {
                    "cliente": sesion["cliente"],
                    "servicio": sesion["servicio"],
                    "fecha": sesion["fecha"],
                    "hora": sesion["hora"],
                },
            }
            sesion["pendiente"] = pendiente
        return {
            "respuesta": _resumen_pendiente(sesion["pendiente"]),
            "estado_sesion": {k: v for k, v in sesion.items()},
        }

    if intencion in {"fuera_de_alcance", "fuera", "no_relacionado"}:
        return {
            "respuesta": "Eso no parece estar relacionado con Rata mania. Puedo ayudarte con catálogo, disponibilidad, reservas o cancelaciones.",
            "estado_sesion": {k: v for k, v in sesion.items()},
        }

    return {
        "respuesta": (
            "¡Hola! Bienvenido a Rata mania. "
            "Puedo ayudarte a ver nuestro catálogo, consultar disponibilidad, "
            "reservar, cancelar o actualizar una reserva. ¿Qué necesitas?"
        ),
        "estado_sesion": {k: v for k, v in sesion.items()},
    }


def _resumen_pendiente(pendiente: dict) -> str:
    d = pendiente["datos"]
    if pendiente["accion"] == "reservar":
        return (
            f"Resumen: {d['cliente']} — {d['servicio']} "
            f"el {d['fecha']} a las {d['hora']}. "
            "Responde CONFIRMAR para guardar o ABORTAR para descartar."
        )
    if pendiente["accion"] == "cancelar":
        return (
            f"Vas a cancelar la reserva {d['codigo']}. "
            "Responde CONFIRMAR para proceder o ABORTAR para descartar."
        )
    return "¿Confirmas la operación pendiente? Responde CONFIRMAR o ABORTAR."


def _normalizar_cliente(nombre: str) -> str:
    """Normaliza el nombre del cliente eliminando caracteres no deseados."""
    nombre = re.sub(r"[^a-zA-ZáéíóúñÁÉÍÓÚÑ\s]", "", nombre)
    nombre = re.sub(r"\s+", " ", nombre)  # Reemplaza multiples espacios por uno solo
    return nombre.strip().title()
