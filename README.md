# Chat_Bot_Rata_Mania

> **Entrega Segundo Corte -==== Creación de Chatbots**  
>  Rata_mania es una tienda de reservas donde se consultaran sus productos por medio
>  del chat bot integrado con FastAPI, Gradio y SQLite mas un despliegue hecho en docker
>  y posteriormente se podran crear reservas.

---

##  Integrantes
* **Jhon Farfan** - *desarrollador*
* **Diana Pacheco** - *desarrolladora*

---

##  Enlaces a la Documentación Principal

la documentación extendida y evidencias se encuentran en los siguientes enlaces:

*  [**Presentación del Proyecto - Chatbot (PDF)**](docs/Chatbot.pdf) (Explicación ejecutiva y flujo de trabajo)
*  [**Carpeta de Evidencias**](docs/evidencias/)
*  [**Carpeta de bitacora final (.zip)**](docs/bitacora/) 
---

## 🛠️ Requisitos Previos

* Python 3.10+
* Git
* Docker

---

## ⚙️ Instalación y Configuración

1. **Clonar el repositorio o descargar la carpeta:**
   ```bash
	git clone https://github.com/dCarolina12/Chat_Bot_Rata_Mania.git
	cd Chat_Bot_Rata_Mania/
   ```
   
2. **Configuracion rapida para despliegue:**
   ```bash
	cd docker 
	echo "GROQ_API_KEY=<API_KEY>" > .env
	echo "GROQ_MODEL=openai/gpt-oss-120b" >> .env # otro modelo si lo prefiere
	docker compose up --build
   
   ```

En este punto ya la app deberia de estar corriendo en local desde el puerto 8011
para el servicio api y el 7860 para el servicio gradio, consulte el archivo Dockerfile 
para mas informacion sobre estos dos servicios
