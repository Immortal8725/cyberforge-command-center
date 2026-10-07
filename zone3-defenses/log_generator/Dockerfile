FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends passwd util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home --shell /usr/sbin/nologin cyberforge

WORKDIR /app
COPY generator.py /app/generator.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

USER root
ENTRYPOINT ["/entrypoint.sh"]
