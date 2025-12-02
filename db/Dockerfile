FROM postgres:15

# Install PostGIS and pgvector build dependencies
RUN apt-get update && apt-get install -y \
    postgresql-15-postgis-3 \
    postgresql-15-postgis-3-scripts \
    build-essential \
    git \
    postgresql-server-dev-15 \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector
RUN cd /tmp && \
    git clone --branch v0.6.0 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install && \
    rm -rf /tmp/pgvector

# Clean up build dependencies
RUN apt-get remove -y build-essential git postgresql-server-dev-15 && \
    apt-get autoremove -y

