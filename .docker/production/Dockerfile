FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (build tools, libraries for python C extensions, nodejs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git gcc g++ make \
    python3-dev python3-pip \
    libxml2-dev libxslt1-dev \
    zlib1g-dev gettext curl \
    pkg-config \
    libmysqlclient-dev default-libmysqlclient-dev \
    liblua5.4-dev \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install frontend stylesheet processors
RUN npm install -g sass postcss-cli postcss autoprefixer --silent

WORKDIR /code

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt mysqlclient uwsgi

# Copy application source code
COPY . /code

# Ensure production local_settings.py exists inside the container
RUN cp -n .docker/production/local_settings_production.py /code/dmoj/local_settings.py || true

# Precompile frontend assets in the image
RUN sass resources:sass_processed --no-source-map --style=expanded --quiet && \
    postcss \
        sass_processed/style.css \
        sass_processed/content-description.css \
        sass_processed/table.css \
        sass_processed/ranks.css \
        --use autoprefixer -d resources --no-map

EXPOSE 8001

CMD ["uwsgi", "--ini", "/code/uwsgi.ini"]
