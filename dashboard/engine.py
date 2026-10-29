"""Deterministic, educational routing-protocol discrete-event model.

Not a Cisco IOS emulator. Each tick is an abstract propagation step, NOT a second.
RIP model: distributed hop-count distance vector with split horizon / poison reverse,
periodic and delayed triggered full-vector advertisements (approximation).
OSPF model: per-router LSDB view, failure-LSA flooding, shortest path recomputation.
Counts are modeled message transmissions, not measured bytes/CPU/network performance.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import defaultdict
import heapq
from typing import Optional

INF = 16

@dataclass(frozen=True)
class Edge:
    a: str
    b: str
    cost: int = 1

    @property
    def key(self) -> tuple[str, str]:
        return tuple(sorted((self.a, self.b)))

@dataclass
class Network:
    edges: list[Edge]
    source: str
    destination: str
    failed_edge: tuple[str, str]
    label: str
    failed_edges: tuple[tuple[str, str], ...] | None = None

    @property
    def failures(self):
        return tuple(sorted({tuple(sorted(e)) for e in (self.failed_edges if self.failed_edges is not None else (self.failed_edge,))}))

    @property
    def nodes(self) -> list[str]:
        return sorted({x for e in self.edges for x in (e.a, e.b)}, key=lambda s: int(s[1:]))

    def adjacency(self, excluded=()) -> dict[str, dict[str, int]]:
        exclusions = {tuple(sorted(edge)) for edge in excluded}
        adj: dict[str, dict[str, int]] = {x: {} for x in self.nodes}
        for edge in self.edges:
            if edge.key not in exclusions:
                adj[edge.a][edge.b] = edge.cost
                adj[edge.b][edge.a] = edge.cost
        return adj


def five_router_network(weighted: bool = False) -> Network:
    edges = [Edge('R1','R2',8 if weighted else 1),
             Edge('R2','R4',8 if weighted else 1),
             Edge('R1','R3'), Edge('R3','R5'), Edge('R5','R4')]
    return Network(edges, 'R1', 'R4', ('R2','R4'),
                   'Five-router diamond' + (' — unequal costs' if weighted else ''))


def scale_network(n: int) -> Network:
    if n == 5:
        return five_router_network()
    if n < 5 or n > 40:
        raise ValueError('Router count must be between 5 and 40')
    edges = []
    seen = set()
    def add(a, b):
        k = tuple(sorted((a,b)))
        if k not in seen:
            edges.append(Edge(a,b));seen.add(k)
    # Ring guarantees a second path after the loss of any one connection.
    for i in range(1, n + 1):
        add(f'R{i}', f'R{1 + (i % n)}')
    # Deterministic shortcuts to model a non-trivial enterprise-like topology.
    for i in range(1,n + 1, 4):
        j=1+((i+2)%n)
        if f'R{i}' != f'R{j}':
            add(f'R{i}', f'R{j}')
    destination = f'R{n//2 + 1}'
    interim = Network(edges, 'R1', destination, ('R1','R2'), f'{n}-router ring with chords')
    path=shortest_path(interim.adjacency(), interim.source, interim.destination, 'RIP')
    if len(path)<2:
        raise AssertionError('Unexpected disconnected topology')
    # Prefer a path edge one hop away from the source, so failure notification must propagate.
    idx = 1 if len(path) >= 3 else 0
    interim.failed_edge=(path[idx],path[idx+1])
    return interim


def shortest_path(adj: dict[str,dict[str,int]], source: str, destination: str, protocol='OSPF') -> list[str]:
    if source not in adj or destination not in adj:
        return []
    heap=[(0,(source,),source)]
    best={}
    while heap:
        cost,path,u=heapq.heappop(heap)
        if u in best:
            continue
        best[u]=cost
        if u==destination:
            return list(path)
        for v in sorted(adj[u]):
            if v not in best:
                edge=1 if protocol=='RIP' else adj[u][v]
                heapq.heappush(heap,(cost+edge,path+(v,),v))
    return []


def all_routes(adj, protocol):
    return {u:{v: shortest_path(adj,u,v,protocol) for v in adj} for u in adj}


def next_hops(adj, protocol):
    paths=all_routes(adj,protocol)
    return {u:{d:(path[1] if len(path)>1 else u if u==d else None) for d,path in paths[u].items()}
            for u in adj}


def packet_probe(nexts, physical_adj, source, destination):
    u=source
    trail=[u]
    for _ in range(len(physical_adj)*2+2):
        if u==destination:
            return True,trail,'delivered'
        v=nexts.get(u,{}).get(destination)
        if not v or v not in physical_adj.get(u,{}):
            return False,trail,'missing or invalid next hop'
        if v in trail:
            trail.append(v)
            return False,trail,'forwarding loop'
        trail.append(v)
        u=v
    return False,trail,'TTL exhausted'


def rip_initial_vectors(network):
    adj=network.adjacency()
    routes=all_routes(adj,'RIP')
    vectors={}
    for u in adj:
        vectors[u]={}
        for dest,path in routes[u].items():
            metric = len(path)-1 if path else INF
            vectors[u][dest]=(min(metric, INF), (path[1] if len(path)>1 else u) if metric<INF else None)
    return vectors


def advertise(vector, receiver):
    return {dest: (INF if hop==receiver and dest!=receiver else metric)
            for dest,(metric,hop) in vector.items()}


def new_rip_vector(router, physical_adj, heard, nodes):
    vals={dest: (0,router) if router==dest else (INF,None) for dest in nodes}
    for dest in nodes:
        if dest==router:
            continue
        candidates=[]
        for neighbor in sorted(physical_adj[router]):
            metric=heard[router].get(neighbor,{}).get(dest,INF)
            if metric+1 < INF:
                candidates.append((metric+1,neighbor))
        if candidates:
            vals[dest]=min(candidates)
    return vals


def run_experiment(network: Network, protocol: str, *, horizon=48,
                   rip_trigger_delay=3, rip_periodic_interval=12):
    """Simulate ONE permanent failed link after an initially converged topology.

    Returns per-tick trace, convergence in ABSTRACT TICKS, protocol update
    transmission counts, forwarding success and route recomputation events.
    """
    protocol=protocol.upper()
    if protocol not in ('RIP','OSPF'):
        raise ValueError('Unsupported protocol')
    if horizon<8 or rip_periodic_interval<1 or rip_trigger_delay<1:
        raise ValueError('Invalid model parameters')
    original=network.adjacency()
    failures=network.failures
    physical=network.adjacency(excluded=failures)
    if any(e not in {edge.key for edge in network.edges} for e in failures):
        raise ValueError('Failed link is not in network')
    nodes=network.nodes
    queue=[];sequence=0;event_count=0
    scheduled=set()
    messages=0;periodic_messages=0;triggered_messages=0;lsa_messages=0
    recalcs=0

    def put(t,typ,node,payload=None):
        nonlocal sequence
        sequence+=1
        heapq.heappush(queue,(t,sequence,typ,node,payload))

    if protocol=='RIP':
        vectors=rip_initial_vectors(network)
        heard={r:{nb:advertise(vectors[nb],r) for nb in original[r]} for r in nodes}
        def schedule_changed(router,t):
            key=(router,t+rip_trigger_delay)
            if key not in scheduled:
                scheduled.add(key);put(t+rip_trigger_delay,'send',router,'triggered')
        endpoints=sorted({end for edge in failures for end in edge})
        for a,b in failures:
            heard[a].pop(b,None)
            heard[b].pop(a,None)
        for end in endpoints:
            updated=new_rip_vector(end,physical,heard,nodes)
            recalcs+=1
            if updated!=vectors[end]:
                vectors[end]=updated;schedule_changed(end,0)
        for tick in range(rip_periodic_interval,horizon+1,rip_periodic_interval):
            for node in nodes:
                put(tick,'send',node,'periodic')
    else:
        knowledge={node:set() for node in nodes}
        known_routes={node: next_hops(original,'OSPF')[node] for node in nodes}
        for changed_edge in failures:
            for end in changed_edge:
                knowledge[end].add(changed_edge)
        for end in sorted({node for edge in failures for node in edge}):
            known_routes[end]=next_hops(network.adjacency(excluded=knowledge[end]),'OSPF')[end]
            recalcs+=1
            for changed_edge in sorted(knowledge[end]):
                for nb in physical[end]:
                    put(1,'lsa',nb,(end,changed_edge))
                    messages+=1;lsa_messages+=1

    timeline=[]
    for tick in range(horizon+1):
        while queue and queue[0][0]<=tick:
            _,_,typ,recipient,payload=heapq.heappop(queue)
            event_count+=1
            if protocol=='RIP':
                if typ=='send':
                    mode=payload
                    for nb in physical[recipient]:
                        put(tick+1,'rip_update',nb,(recipient,advertise(vectors[recipient],nb)))
                        messages+=1
                        if mode=='periodic':periodic_messages+=1
                        else:triggered_messages+=1
                elif typ=='rip_update':
                    sender,advertised=payload
                    if sender not in physical[recipient]:
                        continue
                    heard[recipient][sender]=advertised
                    updated=new_rip_vector(recipient,physical,heard,nodes)
                    recalcs+=1
                    if updated!=vectors[recipient]:
                        vectors[recipient]=updated
                        schedule_changed(recipient,tick)
            else:
                if typ=='lsa':
                    sender,edge=payload
                    if edge in knowledge[recipient] or sender not in physical[recipient]:
                        continue
                    knowledge[recipient].add(edge)
                    recalcs+=1
                    known_routes[recipient]=next_hops(network.adjacency(excluded=knowledge[recipient]),'OSPF')[recipient]
                    for nb in physical[recipient]:
                        if nb==sender:continue
                        put(tick+1,'lsa',nb,(recipient,edge))
                        messages+=1;lsa_messages+=1
        if protocol=='RIP':
            hops={r:{d:(info[1] if info[0]<INF else None) for d,info in vectors[r].items()} for r in nodes}
        else:
            hops=known_routes
        delivered,path,reason=packet_probe(hops,physical,network.source,network.destination)
        timeline.append({'tick':tick,'delivered':delivered,'path':' → '.join(path),
                         'path_nodes':path,'reason':reason,
                         'control_messages':messages,'recalculations':recalcs,
                         'source_next_hop':hops[network.source].get(network.destination),
                         'router_states':[
                             {'router':r,'destination':network.destination,
                              'next_hop':hops[r].get(network.destination),
                              'metric':vectors[r][network.destination][0] if protocol=='RIP' else None,
                              'failure_known':None if protocol=='RIP' else bool(knowledge[r])}
                             for r in nodes]})

    final=timeline[-1]['path'] if timeline[-1]['delivered'] else None
    convergence=None
    if final is not None:
        for point in timeline:
            if point['delivered'] and point['path']==final and all(p['delivered'] and p['path']==final for p in timeline[point['tick']:]):
                convergence=point['tick'];break
    drop=sum(not p['delivered'] for p in timeline)
    summary={
        'protocol':protocol,'routers':len(nodes),'edges':len(network.edges),
        'topology':network.label,'failed_link':', '.join('–'.join(edge) for edge in failures),
        'convergence_ticks':convergence,'lost_probes':drop,
        'delivered_probes':len(timeline)-drop,'probe_count':len(timeline),
        'delivery_percent':round(100*(len(timeline)-drop)/len(timeline),1),
        'control_messages':messages,'periodic_messages':periodic_messages,
        'triggered_messages':triggered_messages,'lsa_messages':lsa_messages,
        'routing_recalculations':recalcs,'final_path':final,
        'final_path_hops':len(timeline[-1]['path_nodes'])-1 if final else None,
        'model_only':True
    }
    return {'network':network,'summary':summary,'timeline':timeline}


def compare(network,**kwargs):
    return {p:run_experiment(network,p,**kwargs) for p in ('RIP','OSPF')}


def scalability(sizes=(5,8,12,16,20), **kwargs):
    rows=[]
    for n in sizes:
        net=scale_network(n)
        for protocol,record in compare(net,**kwargs).items():
            rows.append(record['summary'])
    return rows


def cost_example():
    net=five_router_network(weighted=True)
    a=net.adjacency()
    return {'RIP':shortest_path(a,net.source,net.destination,'RIP'),
            'OSPF':shortest_path(a,net.source,net.destination,'OSPF')}
