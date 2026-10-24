#!/usr/bin/env python3
"""Test script para consulta_llm.py sin exponer credenciales en el comando."""

import os
import sys

# Configurar variables de entorno ANTES de importar
os.environ["GROQ_API_KEY"] = "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"
os.environ["GROQ_MODEL"] = "openai/gpt-oss-120b"
os.environ["CHATBOT_API_URL"] = "http://127.0.0.1:8011"

# Importar y ejecutar
from consulta_llm import main

if __name__ == "__main__":
    # Simular entrada del usuario
    test_inputs = [
        "quiero adoptar una rata dumbo",
        "mañana a las 10:00",
        "Juan Perez",
        "confirmar",
        "SALIR"
    ]

    # Monkey patch input
    original_input = __builtins__.input
    input_iter = iter(test_inputs)

    def mock_input(prompt=""):
        try:
            val = next(input_iter)
            print(f"{prompt}{val}")
            return val
        except StopIteration:
            raise EOFError

    __builtins__.input = mock_input

    try:
        main()
    finally:
        __builtins__.input = original_input