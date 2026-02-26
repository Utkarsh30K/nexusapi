FROM postgres:16-alpine

# Set timezone
ENV TZ=UTC

# Copy custom PostgreSQL config
COPY postgres.conf /etc/postgresql/postgresql.conf

# Run PostgreSQL with custom config
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
