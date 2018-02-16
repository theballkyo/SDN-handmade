from netaddr import *
import database
import pprint

mongo = database.get_mongodb()

if __name__ == '__main__':
    routes = mongo.route.find()
    # pprint.pprint(routes.count())
    for route in routes:
        ip = IPNetwork("{}/{}".format(route['dest'], route['mask']))

        if ip.size == 1:
            start_ip = ip.first
            end_ip = ip.first
        elif ip.size == 2:
            start_ip = ip.first
            end_ip = ip.last
        else:
            start_ip = ip.first + 1
            end_ip = ip.last - 1

        # print("Start: {}, End: {}".format(start_ip, end_ip))
        mongo.route.update_one({
            '_id': route['_id']
        }, {
            '$set': {
                'start_ip': start_ip,
                'end_ip': end_ip
            }
        })
        print("Route {} - {} is update".format(route['dest'], route['mask']))
