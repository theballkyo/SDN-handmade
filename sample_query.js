// Group netflow
db.sdn_test2.netflow.aggregate([
    // Match stage
    {
        $match: {
            first_switched: {
                $lte: Date("2016-05-16T04:18:00.000Z")
            }
        }
    },
    {
        $group: {
            _id: {
                "ipv4_dst_addr": "$ipv4_dst_addr",
                "ipv4_dst_port": "$ipv4_dst_port",
                "l4_src_port": "$l4_src_port",
                "l4_dst_port": "$l4_dst_port"
            },
            total_in_bytes: { $sum: "$in_bytes" },
            total_in_pkts: { $sum: "$in_pkts" }
        }
    },
    {
        $sort: {
            total_in_bytes: -1,
            total_in_pkts: -1
        }
    }
])