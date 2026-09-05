FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.lock ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.lock && pip check
COPY pyproject.toml README.md ./
COPY app ./app
COPY evaluation ./evaluation
COPY load_tests ./load_tests
COPY data ./data
COPY .streamlit ./.streamlit
RUN pip install --no-deps --no-build-isolation . && pip check

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/storage/chroma /app/results /home/appuser/.cache/huggingface \
    && chown -R appuser:appuser /app /home/appuser/.cache
USER appuser

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit", "run", "app/ui/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
