FROM python:3.12-slim

# uv makes installs fast and uses the same lock file as local development.
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY .streamlit ./.streamlit
RUN uv sync --frozen --no-dev

# Don't run as root inside the container.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8501
# Render (and most hosts) tell the app which port to use through $PORT; 8501 locally.
CMD uv run --no-sync streamlit run src/pulseops/app.py --server.address=0.0.0.0 --server.port=${PORT:-8501}
