database = {
    'default': {
        'driver': 'mongodb',  # Currently support only mongo
        # 'username': '',
        # 'password': '',
        'uri': 'mongodb://192.168.99.100:27017/',
        'database': 'sdn_test2',
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
