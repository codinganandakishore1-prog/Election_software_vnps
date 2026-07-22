# MySQL 8 for local Compose / Render private service.
# Data directory must be a persistent disk mounted at /var/lib/mysql.

FROM mysql:8.0

ENV MYSQL_DATABASE=election_db \
    MYSQL_USER=election \
    MYSQL_PASSWORD=election \
    MYSQL_ROOT_PASSWORD=rootchange

EXPOSE 3306
