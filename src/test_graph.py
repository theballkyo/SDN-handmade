import graphs
import pprint
import sdn_handmade as sdn

r1 = sdn.CiscoRouter(ip='192.168.1.1')
r2 = sdn.CiscoRouter(ip='192.168.1.2')
r3 = sdn.CiscoRouter(ip='192.168.1.3')
r4 = sdn.CiscoRouter(ip='192.168.1.4')

graph = {
    r1: [r2, r3],
    r2: [r1, r4],
    r3: [r1],
    r4: [r2]
}

graph = graphs.Graph(graph)

pprint.pprint(graph)
pprint.pprint(graph.vertices())
pprint.pprint(graph.edges())
pprint.pprint(graph.find_path(r1, r4))
