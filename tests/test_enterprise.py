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


def test_scaled_network_preserves_enterprise_links_and_endpoints():
    from enterprise import expanded_enterprise_network
    original=enterprise_network(False)
    for size in (12,16,20,28,36):
        net=expanded_enterprise_network(size)
        assert len(net.nodes)==size
        assert all(edge in net.edges for edge in original.edges)
        assert (net.source,net.destination,net.failed_edge)==('R1','R12',('R2','R12'))


def test_simultaneous_failures_never_forward_on_broken_links():
    net=enterprise_network(False,(('R2','R12'),('R8','R12')))
    assert len(net.failures)==2
    for result in compare(net).values():
        assert result['timeline'][-1]['delivered']
        for point in result['timeline']:
            assert all(tuple(sorted((a,b))) not in net.failures for a,b in zip(point['path_nodes'],point['path_nodes'][1:]))


def test_multiple_breaks_can_disconnect_source():
    net=enterprise_network(False,(('R1','R2'),('R1','R3'),('R1','R4')))
    for result in compare(net).values():
        assert result['summary']['convergence_ticks'] is None
        assert result['summary']['lost_probes']==result['summary']['probe_count']


def test_empty_failure_selection_keeps_everything_working():
    for result in compare(enterprise_network(False,())).values():
        assert result['summary']['lost_probes']==0
        assert result['summary']['control_messages']>=0
