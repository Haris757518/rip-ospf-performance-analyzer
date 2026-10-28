import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dashboard'))
from engine import five_router_network, scale_network, shortest_path, compare, cost_example, packet_probe, next_hops, run_experiment


def test_base_two_hop_route():
    net=five_router_network()
    assert shortest_path(net.adjacency(),net.source,net.destination,'RIP')==['R1','R2','R4']
    assert shortest_path(net.adjacency(),net.source,net.destination,'OSPF')==['R1','R2','R4']


def test_cost_demonstration():
    assert cost_example()=={'RIP':['R1','R2','R4'], 'OSPF':['R1','R3','R5','R4']}


def test_failure_has_alternative_path():
    net=five_router_network()
    physical=net.adjacency(excluded=[net.failed_edge])
    assert shortest_path(physical,'R1','R4','RIP')==['R1','R3','R5','R4']


def test_t0_has_dropped_packet_for_both_protocols():
    pair=compare(five_router_network())
    assert not pair['RIP']['timeline'][0]['delivered']
    assert not pair['OSPF']['timeline'][0]['delivered']


def test_both_converge_without_magic_milliseconds():
    pair=compare(five_router_network())
    for proto in ('RIP','OSPF'):
        data=pair[proto]
        assert data['summary']['convergence_ticks'] is not None
        assert data['summary']['final_path']=='R1 → R3 → R5 → R4'
        assert data['timeline'][-1]['delivered']
        assert data['summary']['model_only'] is True
        assert data['summary']['control_messages']>0
    assert pair['OSPF']['summary']['convergence_ticks']<pair['RIP']['summary']['convergence_ticks']


def test_rip_trigger_delay_changes_route_recovery():
    net=five_router_network()
    fast=run_experiment(net,'RIP',rip_trigger_delay=1)
    slow=run_experiment(net,'RIP',rip_trigger_delay=6)
    assert fast['summary']['convergence_ticks']<slow['summary']['convergence_ticks']


def test_scalability_graphs_connected_with_backup():
    for n in (5,8,12,16,20,28,36):
        net=scale_network(n)
        assert len(net.nodes)==n
        assert shortest_path(net.adjacency(excluded=[net.failed_edge]),net.source,net.destination,'RIP')
        result=compare(net)
        assert all(data['summary']['convergence_ticks'] is not None for data in result.values())


def test_packets_lost_match_trace():
    for proto,record in compare(five_router_network()).items():
        summary=record['summary'];history=record['timeline']
        assert summary['lost_probes']==sum(not x['delivered'] for x in history)
        assert summary['probe_count']==len(history)
        assert summary['delivered_probes']+summary['lost_probes']==summary['probe_count']


def test_no_dv_hop_count_over_15():
    net=scale_network(36)
    rip=run_experiment(net,'RIP',horizon=80)
    assert rip['summary']['convergence_ticks'] is not None


def test_poison_reverse_prevents_false_immediate_shortcut():
    net=five_router_network()
    first=run_experiment(net,'RIP')['timeline'][0]
    assert not first['delivered']
    assert first['path']=='R1 → R2'
