FROM python:3.6-slim

# For Netflow server
EXPOSE 23456
# For APIs
EXPOSE 8080

RUN set -ex \
    && apt-get update \
    && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /data

COPY requirements.txt /data/requirements.txt

RUN pip install -r requirements.txt

COPY . /data

CMD = ["python", "main.py"]