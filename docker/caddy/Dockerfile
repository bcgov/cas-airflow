FROM caddy:2.2.1-alpine

COPY Caddyfile .
RUN chmod g=u /etc/passwd && \
    ./fix-permissions .
USER 1001
