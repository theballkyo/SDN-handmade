FROM python:3.6-slim

# For Netflow server
EXPOSE 23456

# For APIs
EXPOSE 5001

RUN set -ex \
    && apt-get update \
    && apt-get install -y gcc build-essential --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /data

COPY requirements.txt /data/requirements.txt

RUN pip install -r requirements.txt

COPY . /data

RUN apt-get remove gcc build-essential -y

CMD = ["python", "main.py", "--db", "default"]