FROM python:3.14.0-slim-trixie AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.17 /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_DEV=1 \
    UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-install-project
COPY src/ src/
COPY README.md .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.14.0-slim-trixie AS production
RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr libgl1
RUN groupadd -g 101 app \
    && useradd -u 101 -g app --system -m -s /usr/sbin/nologin app \
    && install -d -o app -g app /home/app/logs \
    && install -d -o app -g app /home/app/output \
    && install -d -o app -g app /home/app/tessdata
COPY --from=build /app/.venv/ /app/.venv/
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    LOG_DIR="/home/app/logs" \
    OUTPUT_DIR="/home/app/output" \
    TESSDATA_DIR="/home/app/tessdata"
WORKDIR /home/app/data
USER app
ENTRYPOINT ["ai-summarizer"]
