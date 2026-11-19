FROM python:3.15-slim
WORKDIR /app
COPY watchdog.py /app/watchdog.py
COPY jobs.example.json /app/jobs.example.json
RUN useradd --system --uid 10001 watchdog && mkdir -p /data /outputs && chown watchdog:watchdog /data
USER watchdog
EXPOSE 8765
CMD ["python", "-u", "/app/watchdog.py"]
