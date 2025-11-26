# data/Dockerfile (propuesto)
FROM python:3.12-slim

# Evitar buffers en Python para ver logs en tiempo real
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/home/suria/app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    wget \
    unzip \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios
RUN useradd --create-home --shell /bin/bash suria
WORKDIR /home/suria/app
RUN chown -R suria:suria /home/suria/app

# Instalar dependencias Python como root, luego cambiar a usuario no-root
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copiar el código de la carpeta `data/`
COPY . /home/suria/app/

# Ajustar permisos y cambiar al usuario
RUN chown -R suria:suria /home/suria/app
USER suria

# ENV CONFIG_OBJECT_NAME="sources_config.json"
# ENV CONFIG_POLL_INTERVAL=300

# Workdir ya es /home/suria/app
WORKDIR /home/suria/app

ENTRYPOINT ["python"]
CMD ["-m", "scheduler.runner"]

# Crear imagen en local
# docker build -f data/Dockerfile -t suria-data:dev .

# Ejecutar contenedor en local
# docker run -d --name suria-test `
#   -e PYTHONUNBUFFERED=1 `
#   -e CONFIG_POLL_INTERVAL=60 `
#   -v "${PWD}\data\logs_config\logs:/home/suria/app/logs_config/logs" `
#   -v "${PWD}\data\workflows\sources_config.json:/home/suria/app/workflows/sources_config.json:ro" `
#   suria-data:dev

# Seguir logs en local
# docker logs -f --tail 200 suria-test
