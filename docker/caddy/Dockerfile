FROM caddy:2.2.1-builder AS builder

RUN xcaddy build \
    --with github.com/gamalan/caddy-tlsredis

FROM caddy:2.2.1

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
COPY root .
RUN chmod g=u /etc/passwd && \
    ./fix-permissions .
USER 1001
