COPY root /

WORKDIR /app
RUN wget https://github.com/wal-g/wal-g/releases/download/v0.2.15/wal-g.linux-amd64.tar.gz /
    && tar -zxvf wal-g.linux-amd64.tar.gz /
    && ./wal-g --help
RUN chmod g=u /etc/passwd && \
    /usr/libexec/fix-permissions /app
USER 1001

