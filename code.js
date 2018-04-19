db.getCollection('device').aggregate([
    {
        $project: {
            uptime: 1,
            routes: {
                $filter: {
                    input: "$routes",
                    as: "route",
                    cond: {
                        $and:
                            [
                                {$eq: ["$$route.ipCidrRouteProto", 13]},
//                         { $eq: [ "$$route", null ] },
//                         { $exists: [ "$$route", true ] }
//                         { $size: [ "$$route", 1]}
                        ]
                    },

                }
            }
        }
    },
    {
        '$match': {
            'routes.1': {'$exists': true}
        }
    }
])


db.getCollection('device').aggregate([
    {
        $match: {"interfaces.ipv4_address": "192.168.2.2"}
    },
    {
        $project: {
            interfaces: {
                $filter: {
                    input: "$interfaces",
                    as: "interface",
                    cond: {
                        $or: [
                            {$eq: ["$$interface.ipv4_address", "192.168.2.2"]},
                            {$eq: ["$$interface.ipv4_address", "192.168.2.1"]}
                        ]
                    }
                }
            },
            _id: 0
        }
    }
])

// Counting flow using
db.getCollection('netflow').aggregate([
    {
        $match: {
            from_ip: "10.0.0.1",
            direction: 0
        }
    },
    {
        '$project': {
            from_ip: 1,
            first_switched: 1,
            last_switched: 1,
            ipv4_src_addr: 1,
            ipv4_dst_addr: 1,
            in_bytes_per_sec: {
                $cond: [
                    {$eq: ["$in_pkts", 1]},
                    "$in_bytes",
                    {$divide: ["$in_bytes", {$divide: [{$subtract: ["$last_switched", "$first_switched"]}, 1000]}]}
                ]
            },
            in_pkts: 1,
            diff: {
                $subtract: ["$last_switched", "$first_switched"]
            },
            in_bytes: 1
        }
    },
    {
        '$project': {
            from_ip: 1,
            first_switched: 1,
            last_switched: 1,
            ipv4_src_addr: 1,
            ipv4_dst_addr: 1,
            in_pkts: 1,
            diff: 1,
            in_bytes_per_sec: 1,
            in_bytes: 1,
            total_in_bytes: {
                $cond: [
                    {$gte: ["$first_switched", ISODate("2018-03-14T16:50:00.000Z")]}, // first_switched > start_range
                    "$in_bytes",
                    {$multiply: [{$divide: [{$subtract: ["$last_switched", ISODate("2018-03-14T16:50:00.000Z")]}, 1000]}, "$in_bytes_per_sec"]}
                    // "$in_bytes_per_sec" // (last_switched - start_range) * in_bytes_per_sec
                ]
            }
        }
    },
    {
        $match: {
            total_in_bytes: {$gte: 0}
        }
    },
    {
        $group: {
            _id: {
                ipv4_src_addr: "$ipv4_src_addr",
                ipv4_dst_addr: "$ipv4_dst_addr"
//                 from_ip: "$from_ip"
            },
            total_in_bytes: {$sum: "$total_in_bytes"}
//         first_switched: "$first_switched",
//         last_switched: "$last_switched",
//         ipv4_src_addr: "$ipv4_src_addr",
//         ipv4_dst_addr: "$ipv4_dst_addr",
//         in_pkts: "$in_pkts",
//         diff: "$diff",
//         in_bytes_per_sec: "$in_bytes_per_sec",
//         in_bytes: "$in_bytes",
//         total_in_bytes: "$total_in_bytes"
        }
    },
    {
        $sort: {
            total_in_bytes: -1
        }
    },
    {
        $skip: 0
    },
    {
        $limit: 100
    }
])

// Select only interface in matching
db.items.aggregate(
      {$unwind:"$items"},
      {$match:{"items.return":true}}
)