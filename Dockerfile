FROM python:3.15-slim
WORKDIR /app
COPY watchdog.py /app/watchdog.py
COPY jobs.example.json /app/jobs.example.json
RUN mkdir -p /data /outputs && chown 10001:10001 /data
USER 10001:10001
EXPOSE 8765
CMD ["python", "-u", "/app/watchdog.py"]
