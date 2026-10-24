#!/bin/bash
ruta=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ -z "$1" ]]; then
	OFFSET=0
	if [[ -f "$ruta"/scripts/offset.dat ]]; then
		OFFSET=$(<"$ruta"/scripts/offset.dat)
	fi

	if [[ -z "$OFFSET" || "$OFFSET" == 0 ]]; then
		OFFSET=1
	fi
	HEAD=12
	OFFSET=$((OFFSET + 0))
	offsetmod=$((OFFSET + 1))
	echo "$OFFSET"
	CONTENIDO=$(tail -n +"$offsetmod" "$ruta"/reservas.json | head -n "$HEAD")
	echo "$CONTENIDO"
	codigo=$(echo "$CONTENIDO" | grep "codigo" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	cliente=$(echo "$CONTENIDO" | grep "cliente" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	item=$(echo "$CONTENIDO" | grep "item" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	fecha=$(echo "$CONTENIDO" | grep "fecha" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	hora=$(echo "$CONTENIDO" | grep "hora" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	precio_cop=$(echo "$CONTENIDO" | grep "precio_cop" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	duracion=$(echo "$CONTENIDO" | grep "duracion_minutos" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	estado=$(echo "$CONTENIDO" | grep "estado" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	creada_en=$(echo "$CONTENIDO" | grep "creada_en" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	cancelada=$(echo "$CONTENIDO" | grep "cancelada_en" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')

	#TAIL=$(wc -l < "$ruta"/reservas.json)
	TAIL=$((OFFSET + HEAD))
	sqlite3 "$ruta"/ratas.db "INSERT INTO reserva (codigo, cliente, item, fecha, hora, precio_cop, duracion, estado, creada, cancelada) VALUES ('$codigo', '$cliente', '$item', '$fecha', '$hora', $precio_cop, '$duracion', '$estado', '$creada_en', '$cancelada');"
	echo "$TAIL" > "$ruta"/scripts/offset.dat
else
	CODIGO="$1"
	CONTENIDO=$(cat "$ruta"/reservas.json | grep "$CODIGO" -A 9)
	cancelada=$(echo "$CONTENIDO" | grep "cancelada_en" | awk '{print $2}' | cut -d "," -f1 | tr -d '"')
	sqlite3 "$ruta"/ratas.db "UPDATE reserva SET cancelada = '$cancelada', estado = 'cancelada' WHERE codigo = '$CODIGO';"
fi
