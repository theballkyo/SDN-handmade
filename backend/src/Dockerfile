FROM python:3.5-slim

# For Netflow server
EXPOSE 23456
# For APIs
EXPOSE 8080

RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /data

COPY . /data

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]