## Requirements

values in postgresql.conf need to be set to:

wal_level=replica
archive_mode=on
archive_command='sh /usr/local/bin/archive.sh %p' -- This needs to be set to our archive.sh file (not necessarily in user/local...)
archive_timeout=60

This should be done in the deployment for the postgres cluster as updating these values requires a restart of postgres.


## Resources

wal-g github:
https://github.com/wal-g/wal-g

wal-g commands & configs
https://github.com/wal-g/wal-g/blob/master/PostgreSQL.md

wal-g walkthrough (using s3):
https://www.fusionbox.com/blog/detail/postgresql-wal-archiving-with-wal-g-and-s3-complete-walkthrough/644/

postgres write-ahead-logging
https://www.postgresql.org/docs/9.0/wal-intro.html
https://www.postgresql.org/docs/9.0/runtime-config-wal.html

archive/recovery:
https://www.postgresql.org/docs/current/runtime-config-wal.html#RUNTIME-CONFIG-WAL-RECOVERY-TARGET
https://gist.github.com/pohzipohzi/2f111d11ae0469266ddf50a5d71bfd60
