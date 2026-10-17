# Image untuk TrailGuard. Di LinuxONE (s390x), image dasar harus mendukung linux/s390x.
# python:3.11-slim umumnya mendukung s390x -- VERIFIKASI dengan: podman pull python:3.11-slim && podman image inspect ... | grep Arch
# Alternatif jika gagal: registry.access.redhat.com/ubi9/python-311
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY configs ./configs
COPY scripts ./scripts
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["python", "-m", "trailguard.api.app"]
