import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dashboard'))
from core import route_for, validate_records, packet_delivery

def test_baseline():
    for protocol in ('RIP','OSPF'):
        route=route_for(protocol,'baseline')
        assert route.routers==('R1','R2','R4')
        assert route.hops==2

def test_failover():
    for protocol in ('RIP','OSPF'):
        assert route_for(protocol,'failover').routers==('R1','R3','R5','R4')

def test_recovery():
    for protocol in ('RIP','OSPF'):
        assert route_for(protocol,'recovery').routers==('R1','R2','R4')

def test_cost_demo():
    assert route_for('RIP','cost_demo').routers==('R1','R2','R4')
    assert route_for('OSPF','cost_demo').routers==('R1','R3','R5','R4')
    assert route_for('OSPF','cost_demo').metric == 30

def test_validation_good():
    row=dict(protocol='RIP',experiment='failover',trial=1,measurement_basis='Packet Tracer simulated time',convergence_s=5,sent_packets=10,received_packets=9,route_hops=3)
    assert validate_records([row])==[]

def test_validation_rejects_impossible_data():
    row=dict(protocol='RIP',experiment='failover',trial=0,measurement_basis='',convergence_s=-2,sent_packets=5,received_packets=8,route_hops=2.4)
    errors=validate_records([row]); messages=' '.join(e for _,e in errors)
    assert 'positive integer' in messages
    assert 'cannot exceed' in messages
    assert 'cannot be negative' in messages
    assert 'must be an integer' in messages

def test_delivery():
    assert packet_delivery(10,8)==80
    assert packet_delivery(0,0) is None
    assert packet_delivery(10,12) is None


def test_invalid_measurements_are_not_silently_treated_as_blank():
    for value in ('mistyped', 'inf', '-inf', 'nan'):
        row=dict(protocol='RIP',experiment='failover',trial=1,
                 measurement_basis='Packet Tracer simulated time',convergence_s=value)
        assert any('finite number' in message for _, message in validate_records([row]))
