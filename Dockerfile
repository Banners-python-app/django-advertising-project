FROM python:3.13-slim AS build
# ..BYTECODE (tells python npt to write .pyc files to disk, in a container writing this files wastes space)
# ..BUFFERED (forces std op and errors to be sent to terminal or log aggregation system like cloudwatch/datadog)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /build

# Install system dependencies required for building Python packages (like psycopg2)
# We clean up the apt cache immediately to keep the build layer small
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .

# Create python "wheels" (pre-compiled binaries) instead of installing directly
# This uses your BuildKit cache correctly
# --mount=type=cache,target=/root/.cache/pip (mounts a persistent folder on host machine, if we run build 2nd time,pip pulls from host instead of doen from internet)
# pip wheel (this qwill pack dependency into compressed .whl files)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# stage 2
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \  
    libpq5 && rm -rf /var/lib/apt/lists/*
# creating grp n user 
RUN addgroup --system django && adduser --system --ingroup django django

# copy the pre-compiled wheels from build stage n install them
COPY --from=build /build/wheels /wheels
COPY --from=build /build/requirements.txt .
RUN pip install --no-cache /wheels/*
COPY . .

# Hand over ownership of the app directory to the non-root user
RUN chown -R django:django /app

RUN SECRET_KEY="dummy-key-for-build" \
    DATABASE_URL="sqlite:///:memory:" \
    python manage.py collectstatic --noinput --clear
USER django
EXPOSE 8000

# Use Gunicorn (Production WSGI) instead of manage.py runserver
# Gunicorn handles multiple concurrent connections efficiently
# gunicorn core.wsgi:application (start gunicorn and tell to look inside core/wsgi.py file & load the application)
CMD [ "gunicorn","core.wsgi:application","--bind","0.0.0.0:8000","--workers","3","--threads","2" ]