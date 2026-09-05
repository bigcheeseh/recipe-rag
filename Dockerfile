# Stage 1: compile the TypeScript page. Pinned base image and lockfile-driven install.
FROM node:24-alpine AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY ui/tsconfig.json ui/index.html ./
COPY ui/src ./src
RUN npm run build

# Stage 2: the service. requirements.txt is fully pinned, so the image is reproducible.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY prompts ./prompts
COPY data/corpus.json data/embeddings.npz ./data/
COPY --from=ui /ui/dist ./ui/dist
# No secrets are baked in: ANTHROPIC_API_KEY arrives from the environment at run time.
RUN useradd --system --uid 10001 app
USER app
ENV PYTHONPATH=/srv/src
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/healthz')"
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT}"]
