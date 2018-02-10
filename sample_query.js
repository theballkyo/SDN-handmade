// Group netflow
db.getCollection('netflow').aggregate([
    // Match stage
    {
        $match: {
            first_switched: {
                $lte: ISODate("2016-05-16T04:20:00.000Z"),
                $gte: ISODate("2016-05-16T04:18:00.000Z")
            },
            l4_dst_port: 443
        }
    },
    {
        $group: {
            _id: {
                "ipv4_dst_addr": "$ipv4_dst_addr",
                "ipv4_src_addr": "$ipv4_src_addr",
                 "l4_dst_port": "$l4_dst_port",
                 "l4_src_port": "$l4_src_port",
//                "first_switched": "$first_switched"
            },
            total_in_bytes: { $sum: "$in_bytes" },
            total_in_pkts: { $sum: "$in_pkts" }
        }
    },
    {
        $sort: {
            total_in_bytes: -1
//             total_in_pkts: -1
        }
    },
    {
        $limit: 10
    },
    {
            "$group": {
                "_id": null,
                "total_flow":
                    {
                        "$sum": 1
                    },
                "data": {
                    "$push": {
                        "_id": "$_id",
                        "total_in_bytes": "$total_in_bytes",
                        "total_in_pkts": "$total_in_pkts"
                    }
                }
            }
        }
])