"""Pure, testable educational routing model and experiment validation.

IMPORTANT: This model computes static shortest paths; it does not emulate RIP/OSPF
message exchange, convergence timers or Cisco Packet Tracer.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from heapq import heappush, heappop
from math import isfinite
from typing import Mapping

ROUTERS = ('R1', 'R2', 'R3', 'R4', 'R5')
LINKS = (('R1', 'R2'), ('R2', 'R4'), ('R1', 'R3'), ('R3', 'R5'), ('R5', 'R4'))
NETWORK_IPS = {
    'PC-A': '192.168.10.10/24', 'R1': '192.168.10.1/24',
    'R4': '192.168.20.1/24', 'PC-B': '192.168.20.10/24',
}
EXPERIMENTS = ('baseline', 'failover', 'recovery', 'cost_demo')
COLUMNS = (
    'protocol', 'experiment', 'trial', 'measurement_basis',
    'convergence_s', 'sent_packets', 'received_packets',
    'route_hops', 'route_path', 'evidence_note'
)


def _edge(a: str, b: str) -> frozenset[str]:
    return frozenset((a, b))


def _adjacency(failed: frozenset[str] | None = None, high_upper_cost: bool = False) -> dict[str, list[tuple[str,int]]]:
    graph: dict[str, list[tuple[str, int]]] = {r: [] for r in ROUTERS}
    for a,b in LINKS:
        if failed == _edge(a,b):
            continue
        w = 100 if high_upper_cost and _edge(a,b) in {_edge('R1','R2'),_edge('R2','R4')} else (10 if high_upper_cost else 1)
        graph[a].append((b,w))
        graph[b].append((a,w))
    for neighbors in graph.values():
        neighbors.sort()
    return graph


@dataclass(frozen=True)
class Route:
    protocol: str
    scenario: str
    routers: tuple[str, ...]
    metric: int | None
    steps: tuple[str, ...]
    note: str

    @property
    def hops(self) -> int | None:
        return len(self.routers)-1 if self.routers else None

    @property
    def path_text(self) -> str:
        return ' → '.join(self.routers) if self.routers else 'No reachable route'


def route_for(protocol: str, scenario: str = 'baseline') -> Route:
    """Compute *expected* routes for a controlled five-router educational graph."""
    if protocol not in ('RIP','OSPF'):
        raise ValueError('Protocol must be RIP or OSPF')
    if scenario not in EXPERIMENTS:
        raise ValueError(f'Scenario must be one of {EXPERIMENTS}')
    failure = _edge('R2','R4') if scenario == 'failover' else None
    graph = _adjacency(failure, high_upper_cost=(scenario == 'cost_demo' and protocol == 'OSPF'))
    if protocol == 'RIP':
        queue = deque(['R1'])
        hops: dict[str, int] = {'R1': 0}
        parent: dict[str, str] = {}
        steps = ['Begin at R1; evaluate all neighbors in ascending order.']
        while queue:
            u = queue.popleft()
            for v,_ in graph[u]:
                if v not in hops:
                    hops[v]=hops[u]+1
                    parent[v]=u
                    queue.append(v)
                    steps.append(f'Discover {v} at {hops[v]} hop(s) from R1 via {u}.')
        metric = hops.get('R4')
        note = 'Hop-minimal path model (BFS). Real RIPv2 uses distributed distance-vector updates and timers.'
    else:
        dist: dict[str, int] = {'R1':0}
        parent = {}
        heap: list[tuple[int,str]] = [(0,'R1')]
        visited: set[str] = set()
        steps = ['Begin at R1 with path cost 0.']
        while heap:
            cost,u = heappop(heap)
            if u in visited: continue
            visited.add(u)
            steps.append(f'Settle {u}: minimum known path cost {cost}.')
            for v,w in graph[u]:
                candidate=cost+w
                if candidate<dist.get(v,float('inf')):
                    dist[v]=candidate
                    parent[v]=u
                    heappush(heap,(candidate,v))
                    steps.append(f'Relax {u} → {v} (cost {w}); best-known cost to {v} becomes {candidate}.')
        metric=dist.get('R4')
        note = 'Dijkstra shortest-path model using illustrative link costs; not live OSPF control-plane traffic.'
    route: list[str]=[]
    if metric is not None:
        node='R4'
        route=[node]
        while node!='R1':
            node=parent[node]
            route.append(node)
        route.reverse()
    return Route(protocol,scenario,tuple(route),metric,tuple(steps),note)


def validate_records(records: list[Mapping]) -> list[tuple[int,str]]:
    """Return row-indexed errors; empty cells are allowed for uncollected measurements."""
    errors: list[tuple[int,str]]=[]
    for idx,row in enumerate(records,1):
        prot=str(row.get('protocol','')).strip()
        experiment=str(row.get('experiment','')).strip()
        if prot not in ('RIP','OSPF'):
            errors.append((idx,'protocol must be RIP or OSPF'))
        if experiment not in EXPERIMENTS:
            errors.append((idx,'experiment must be baseline, failover, recovery or cost_demo'))
        trial = _number(row.get('trial'))
        if trial is None or not trial.is_integer() or trial < 1:
            errors.append((idx,'trial must be a positive integer'))
        nums={x:_number(row.get(x)) for x in ('convergence_s','sent_packets','received_packets','route_hops')}
        for col, val in nums.items():
            raw = row.get(col)
            blank = raw is None or isinstance(raw, str) and not raw.strip()
            missing_number = not isinstance(raw, str) and str(raw) in ('nan', '<NA>')
            if val is None and not blank and not missing_number:
                errors.append((idx, f'{col} must be a finite number or blank'))
        for col,val in nums.items():
            if val is not None and val<0:
                errors.append((idx,f'{col} cannot be negative'))
        for col in ('sent_packets','received_packets','route_hops'):
            val=nums[col]
            if val is not None and not val.is_integer():
                errors.append((idx,f'{col} must be an integer'))
        sent,received=nums['sent_packets'],nums['received_packets']
        if received is not None and sent is None:
            errors.append((idx,'received_packets requires sent_packets'))
        if received is not None and sent is not None and received>sent:
            errors.append((idx,'received_packets cannot exceed sent_packets'))
        if nums['convergence_s'] is not None and str(row.get('measurement_basis','')).strip() in ('','nan','not applicable'):
            errors.append((idx,'convergence_s requires a declared measurement_basis'))
    return errors


def _number(val) -> float | None:
    if val is None or isinstance(val, str) and not val.strip():return None
    try:
        n=float(val)
        return n if isfinite(n) else None
    except (ValueError,TypeError):
        return None


def packet_delivery(sent: int | None, received: int | None) -> float | None:
    if sent is None or received is None or sent<=0 or not(0<=received<=sent):return None
    return 100.0*received/sent
