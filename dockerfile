# 1. Imagen base de Python
FROM python:3.11-slim

# 2. Configuración básica
ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1         
ENV DEBIAN_FRONTEND=noninteractive

# 3. Dependencias del sistema (ejemplo para PDFs)
RUN apt update 
RUN apt install -y --no-install-recommends poppler-utils
RUN rm -rf /var/lib/apt/lists/*

# 4. Carpeta de trabajo dentro del contenedor
WORKDIR /app

# 5. Copiar solo requirements primero (mejor cache)
COPY requirements.txt .

# 6. Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copiar el resto del proyecto
#    (gracias al .dockerignore NO se copiará github-cpu-ocr, .vscode, data/, etc.)
COPY . .

# 8. Comando por defecto para arrancar tu app
CMD ["python", "main.py"]
