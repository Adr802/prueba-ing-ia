FROM python:3.12-slim
WORKDIR /srv
COPY libs/common /libs/common
RUN pip install --no-cache-dir /libs/common
COPY --from=app . ./app
ENV PORT=8100
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
