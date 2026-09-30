FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    python3 \
    python3-pip \
    python3-dev \
    libseccomp-dev \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir dmoj

RUN useradd -m -u 1000 judge && \
    mkdir -p /problems && \
    chmod 777 /problems

USER judge

ENTRYPOINT ["dmoj"]
