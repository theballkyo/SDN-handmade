from urllib.parse import quote

database = {
    'default': {
        'driver': 'mongodb',  # Currently support only mongo
        # 'username': '',
        # 'password': '',
        'uri': "mongodb://username:" + quote('password') + "@127.0.0.1:27017/?ssl=true&ssl_cert_reqs=CERT_NONE",  # Default port 27017
        'database': 'database_name,
        'max_pool_size': 10,
    }
}

rest_api = {
    'host': '0.0.0.0',
    'port': 5000
}

netflow = {
    'bind_ip': '127.0.0.1',
    'bind_port': 23456
}

app = {
    'version': '0.0.1 Beta'
}
