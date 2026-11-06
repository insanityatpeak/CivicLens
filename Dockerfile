# UNTESTED image (Docker was not available when this was written). For Hugging Face Spaces (Docker), Fly.io, Railway, etc.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock
COPY src ./src
COPY data/samples/pothole.jpg data/samples/garbage.jpg ./data/samples/
ENV PYTHONUNBUFFERED=1 PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn civiclens.web.server:app --app-dir src --host 0.0.0.0 --port ${PORT}"]
