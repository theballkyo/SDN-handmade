from database import get_mongodb

mongo = get_mongodb()


def main():
    device_db = mongo.device
    for change in device_db.watch():
        print(change)


if __name__ == '__main__':
    main()
