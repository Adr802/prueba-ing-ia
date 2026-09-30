FROM python:3.12-slim
WORKDIR /srv
RUN pip install --no-cache-dir "mcp>=1.9,<2" "pydantic>=2.7"
COPY --from=app . ./app
COPY scripts ./scripts
CMD ["python", "-m", "app.main"]
