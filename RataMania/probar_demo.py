"""Prueba reproducible sin Groq ni Flowise. No modifica las reservas de la clase."""
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
import main


def probar():
    with TemporaryDirectory() as carpeta:
        archivo = Path(carpeta) / 'reservas.json'
        archivo.write_text('[]', encoding='utf-8')
        original = main.ARCHIVO
        main.ARCHIVO = archivo
        main.SESIONES.clear()
        try:
            with TestClient(main.app) as api:
                fecha = datetime.now(main.ZONA).date() + timedelta(days=2)
                while fecha.weekday() == 6:
                    fecha += timedelta(days=1)
                dia = fecha.isoformat()
                datos = dict(cliente='Laura', servicio='rata_dumbo', fecha=dia, hora='09:00', confirmado=True)

                # ── Endpoints de soporte ────────────────────────────────────
                assert api.get('/servicios').status_code == 200
                horarios_resp = api.get('/disponibilidad', params={'fecha': dia, 'servicio': 'rata_dumbo'}).json()
                assert '09:00' in horarios_resp['horarios'], f"Esperaba 09:00 en {horarios_resp}"

                # ── Validaciones de formato y negocio ───────────────────────
                assert api.post('/reservas', json={**datos, 'confirmado': False}).status_code == 422
                assert api.post('/reservas', json={**datos, 'hora': '25:00'}).status_code == 422
                assert api.post('/reservas', json={**datos, 'servicio': 'inventado'}).status_code == 422
                assert api.post('/reservas', json={**datos, 'hora': '18:00'}).status_code == 409  # fuera de horario
                assert api.post('/reservas', json={**datos, 'fecha': '2000-01-01'}).status_code == 422

                # Domingo cerrado → sin horarios
                domingo = fecha + timedelta(days=(6 - fecha.weekday()) % 7)
                libres_dom = api.get('/disponibilidad', params={'fecha': domingo.isoformat(), 'servicio': 'rata_dumbo'}).json()
                assert libres_dom['horarios'] == [], f"Domingo debería estar cerrado, got {libres_dom}"

                # ── Concurrencia: solo 1 reserva para el mismo horario ──────
                with ThreadPoolExecutor(max_workers=2) as pool:
                    respuestas = list(pool.map(lambda _: api.post('/reservas', json=datos), range(2)))
                assert sorted(r.status_code for r in respuestas) == [201, 409]
                reserva = next(r.json() for r in respuestas if r.status_code == 201)
                codigo = reserva['codigo']
                assert codigo.startswith('PN-')
                assert len(json.loads(archivo.read_text(encoding='utf-8'))) == 1

                # ── Consultar reserva ───────────────────────────────────────
                main.SESIONES.clear()  # La reserva sobrevive a perder el estado en memoria.
                assert api.get('/reservas/' + codigo).json()['estado'] == 'activa'
                assert api.get('/reservas/INEXISTENTE').status_code == 404

                # ── Disponibilidad bloqueada por la reserva ─────────────────
                libres = api.get('/disponibilidad', params={'fecha': dia, 'servicio': 'jaula_equipada'}).json()['horarios']
                assert '09:00' not in libres, "09:00 debería estar bloqueada"
                assert '09:30' in libres, "09:30 debería estar libre"

                # Cruce de intervalos con hora distinta
                r_mov = {**reserva, 'hora': '09:15'}
                libres2 = main.horarios_libres(fecha, 'rata_dumbo', [r_mov])
                assert '09:00' not in libres2 and '09:30' not in libres2 and '10:00' in libres2

                # ── Cancelar reserva ────────────────────────────────────────
                assert api.delete('/reservas/' + codigo).status_code == 422  # sin confirmado
                assert api.delete('/reservas/' + codigo, params={'confirmado': True}).json()['estado'] == 'cancelada'
                # Idempotente: segunda cancelación devuelve 200 con estado cancelada
                assert api.delete('/reservas/' + codigo, params={'confirmado': True}).status_code == 200
                # El horario vuelve a estar libre tras cancelar
                assert '09:00' in api.get('/disponibilidad', params={'fecha': dia, 'servicio': 'rata_dumbo'}).json()['horarios']

                # ── Actualizar reserva ──────────────────────────────────────
                reserva2_resp = api.post('/reservas', json=datos)
                assert reserva2_resp.status_code == 201
                codigo2 = reserva2_resp.json()['codigo']
                upd = api.put('/reservas/' + codigo2, json={'hora': '10:00'})
                assert upd.status_code == 200
                assert upd.json()['hora'] == '10:00'
                assert api.get('/reservas/' + codigo2).json()['hora'] == '10:00'

                # ── Flujo conversacional /chat ──────────────────────────────
                def chat(texto, extraccion=None, sesion='grupo-1'):
                    return api.post('/chat', json={'session_id': sesion, 'mensaje': texto, 'datos': extraccion or {}})

                # Cancelar para dejar el horario libre antes de la prueba de chat
                api.delete('/reservas/' + codigo2, params={'confirmado': True})

                extraccion = {k: v for k, v in datos.items() if k != 'confirmado'}
                extraccion['intencion'] = 'reservar'
                r = chat('Quiero reservar', extraccion).json()
                assert r['estado_sesion']['pendiente']['datos']['hora'] == '09:00', r
                assert len(json.loads(archivo.read_text(encoding='utf-8'))) == 2  # las dos anteriores siguen

                assert 'No hay un resumen' in chat('CONFIRMAR', sesion='grupo-2').json()['respuesta']

                # Corrección de hora antes de confirmar
                r = chat('Mejor a las 10:00', {'intencion': 'continuar', 'hora': '10:00'}).json()
                assert r['estado_sesion']['pendiente']['datos']['hora'] == '10:00', r

                # Pregunta informativa no confirma
                assert 'pendiente' in chat('Cuánto cuesta', {'intencion': 'informacion'}).json()['estado_sesion']
                assert 'pendiente' in chat('Sí', {}).json()['estado_sesion']  # Solo CONFIRMAR autoriza.

                r = chat('CONFIRMAR').json()
                assert 'Reserva registrada' in r['respuesta'], r
                codigo3 = r['estado_sesion']['ultimo_codigo']
                assert api.get('/reservas/' + codigo3).json()['hora'] == '10:00'
                assert 'No hay un resumen' in chat('CONFIRMAR').json()['respuesta']
                assert len(json.loads(archivo.read_text(encoding='utf-8'))) == 3

                # /reset no borra reservas
                chat('/reset')
                assert api.get('/reservas/' + codigo3).json()['estado'] == 'activa'

                # Cancelación conversacional
                chat('Cancelar ' + codigo3, {'intencion': 'cancelar', 'codigo': codigo3})
                assert api.get('/reservas/' + codigo3).json()['estado'] == 'activa'
                assert 'Reserva cancelada' in chat('CONFIRMAR').json()['respuesta']
                assert api.get('/reservas/' + codigo3).json()['estado'] == 'cancelada'

                # El campo confirmado dentro de datos es rechazado
                assert chat('Datos maliciosos', {'intencion': 'continuar', 'confirmado': True}).status_code == 422

                # Horario ocupado entre resumen y confirmación → 409 en chat
                chat('Reservar', extraccion)
                assert api.post('/reservas', json=datos).status_code == 201
                assert chat('CONFIRMAR').status_code == 409
                assert 'pendiente' not in main.SESIONES['grupo-1']

                # Fallo de escritura en disco → 503
                datos_hora11 = {**datos, 'hora': '11:00'}
                antes = archivo.read_text(encoding='utf-8')
                with patch.object(main.os, 'replace', side_effect=OSError('Prueba de disco')):
                    assert api.post('/reservas', json=datos_hora11).status_code == 503
                assert archivo.read_text(encoding='utf-8') == antes

                # Archivo corrupto → 503 sin sobrescribir
                archivo.write_text('{archivo incompleto', encoding='utf-8')
                assert api.post('/reservas', json=datos_hora11).status_code == 503
                assert archivo.read_text(encoding='utf-8') == '{archivo incompleto'

                print('OK: API, JSON, confirmaciones, correcciones, sesiones, concurrencia, cancelación y fallos de almacenamiento.')
        finally:
            main.ARCHIVO = original
            main.SESIONES.clear()


if __name__ == '__main__':
    probar()
