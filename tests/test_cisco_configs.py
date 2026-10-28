from pathlib import Path
from ipaddress import IPv4Interface
import re

ROOT=Path(__file__).resolve().parents[1]


def test_all_routers_have_independent_protocol_configurations():
    for r in range(1,6):
        for protocol in ('RIP','OSPF'):
            file=ROOT/'configs'/'paste_ready'/f'R{r}_{protocol}_COMPLETE.txt'
            content=file.read_text()
            assert f'hostname R{r}' in content
            assert ('router rip' if protocol=='RIP' else 'router ospf 1') in content
            assert 'no shutdown' in content


def test_router_ip_addresses_unique_and_expected_networks():
    addresses=[]
    for r in range(1,6):
        content=(ROOT/'configs'/'base'/f'R{r}_interfaces.txt').read_text()
        for ip,mask in re.findall(r'^\s*ip address (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)',content,re.M):
            addresses.append(IPv4Interface(f'{ip}/{mask}'))
    assert len(addresses)==12
    assert len(set(x.ip for x in addresses))==12
    network_count={}
    for ip in addresses:network_count[str(ip.network)]=network_count.get(str(ip.network),0)+1
    for net in ('10.0.12.0/30','10.0.24.0/30','10.0.13.0/30','10.0.35.0/30','10.0.45.0/30'):
        assert network_count[net]==2
    assert network_count['192.168.10.0/24']==1
    assert network_count['192.168.20.0/24']==1


def test_cost_override_present_on_all_routers():
    for r in range(1,6):
        content=(ROOT/'configs'/'ospf'/f'R{r}_cost_override.txt').read_text()
        assert 'ip ospf cost' in content
