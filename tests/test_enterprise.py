import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dashboard'))
from enterprise import enterprise_network,path_cost
from engine import shortest_path,compare


def test_enterprise_has_redundancy_and_distinct_weighted_routes():
    net=enterprise_network()
    assert len(net.nodes)==12 and len(net.edges)==18
    paths={p:shortest_path(net.adjacency(),net.source,net.destination,p) for p in ('RIP','OSPF')}
    assert paths['RIP']==['R1','R2','R12']
    assert paths['OSPF']==['R1','R3','R5','R8','R12']
    assert path_cost(net,paths['RIP'])==24
    assert path_cost(net,paths['OSPF'])==8
    for edge in net.edges:
        assert shortest_path(net.adjacency(excluded=[edge.key]),net.source,net.destination)


def test_equal_cost_failure_starts_matched_and_recovers():
    net=enterprise_network(False)
    assert shortest_path(net.adjacency(),'R1','R12','RIP')==shortest_path(net.adjacency(),'R1','R12','OSPF')
    pair=compare(net)
    for r in pair.values():
        assert not r['timeline'][0]['delivered']
        assert r['summary']['convergence_ticks'] is not None
        assert r['timeline'][-1]['delivered']


def test_failure_of_unused_legacy_link_does_not_drop_ospf_probes():
    pair=compare(enterprise_network())
    assert pair['OSPF']['summary']['lost_probes']==0
    assert pair['RIP']['summary']['lost_probes']>0
