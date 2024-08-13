#           BASIC FILE SETUP

FROM        python:3.11-slim-bullseye AS base

LABEL       author="Isaac Kogan" maintainer="koganisa@yorku.ca"

#           LINUX PACKAGES

RUN         apt-get update \
            && apt-get -y install git gcc g++ ca-certificates dnsutils curl iproute2 ffmpeg procps tini \
            && useradd -m -d /home/cria cria

FROM        base AS with_packages

#           USER & ENTRYPOINT

USER        cria
ENV         USER=cria HOME=/home/cria
WORKDIR     /home/cria

#           PYTHON PACKAGES

COPY        requirements-1.txt ./
COPY        requirements-2.txt ./

RUN         pip install -r requirements-1.txt
RUN         pip install -r requirements-2.txt

RUN         rm ./requirements-1.txt
RUN         rm ./requirements-2.txt

FROM        with_packages AS final

#           PROJECT SOURCE CODE

COPY        ./.env ./.env
COPY        ./app ./app
COPY        ./criaparse ./criaparse

#           START SERVER

COPY        --chown=cria:cria ./entrypoint.sh /entrypoint.sh
RUN         chmod +x /entrypoint.sh
ENTRYPOINT  ["/usr/bin/tini", "-g", "--"]
CMD         ["/entrypoint.sh"]
