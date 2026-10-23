const API_URL = 'http://localhost:8011';
const fetch = require('node-fetch');

const mensaje = String($input || '').trim();
const session_id = $flow.sessionId || $flow.chatId;

if (!session_id) return 'No se recibió una sesión. Abre una conversación nueva.';

let datos = {};

if (!['confirmar', 'abortar', 'no', '/reset'].includes(mensaje.toLowerCase())) {
    try {
        let rawExtraccion = $extraccion;

        // Si viene envuelto en un objeto de salida del LLM (ej. { text: "..." })
        if (rawExtraccion && typeof rawExtraccion === 'object' && rawExtraccion.text) {
            rawExtraccion = rawExtraccion.text;
        }

        // Parsear si viene como String
        if (typeof rawExtraccion === 'string') {
            const jsonLimpio = rawExtraccion.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '');
            datos = JSON.parse(jsonLimpio);
        } else if (typeof rawExtraccion === 'object' && rawExtraccion !== null) {
            datos = rawExtraccion;
        }

        if (!datos || Array.isArray(datos) || typeof datos !== 'object') {
            datos = {};
        }
    } catch (e) {
        datos = {};
    }
}

try {
    const response = await fetch(API_URL + '/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({ session_id, mensaje, datos }),
        timeout: 8000
    });

    const resultado = await response.json();
    if (typeof resultado.respuesta === 'string') return resultado.respuesta;
    if (response.status === 422) return 'La API rechazó los datos (422 Unprocessable Entity).';

    return 'La API no devolvió un resultado válido. Revisa la terminal del backend.';
} catch (err) {
    return `Error de conexión con la API: ${err.message}`;
}