# Packet Tracer topology and physical connections

**Devices:** 5 x Cisco 2911 routers; 2 x Cisco 2960 switches; 2 x PC-PT; 9 Ethernet cables.

```text
                 R2
               /    \
 PC-A--SW1--R1        R4--SW2--PC-B
               \      /
                R3--R5
```

## Port-to-port cable map

| From | To | IPv4 subnet |
|---|---|---|
| PC-A Fa0 | SW1 Fa0/1 | 192.168.10.0/24 |
| SW1 Fa0/2 | R1 Gi0/0 | 192.168.10.0/24 |
| R1 Gi0/1 | R2 Gi0/0 | 10.0.12.0/30 |
| R2 Gi0/1 | R4 Gi0/1 | 10.0.24.0/30 |
| R1 Gi0/2 | R3 Gi0/0 | 10.0.13.0/30 |
| R3 Gi0/1 | R5 Gi0/0 | 10.0.35.0/30 |
| R5 Gi0/1 | R4 Gi0/2 | 10.0.45.0/30 |
| R4 Gi0/0 | SW2 Fa0/2 | 192.168.20.0/24 |
| SW2 Fa0/1 | PC-B Fa0 | 192.168.20.0/24 |

## PC Desktop > IP Configuration

- PC-A IP: `192.168.10.10`, mask: `255.255.255.0`, gateway: `192.168.10.1`
- PC-B IP: `192.168.20.10`, mask: `255.255.255.0`, gateway: `192.168.20.1`

## Setup
1. Place and cable devices per the table.
2. Paste the base interface config from `configs/base` into the matching router.
3. Confirm that each interface is up with `show ip interface brief`.
4. Save **a separate Packet Tracer project** for each protocol.
5. For `RIP_Experiment.pkt` paste the matching config from `configs/rip` onto all five routers.
6. For `OSPF_Experiment.pkt` paste the matching config from `configs/ospf` onto all five routers.
7. Do not run RIP and OSPF simultaneously in a comparative configuration; avoid route-selection biases from administrative distance.
8. Wait for routes to stabilize, then test from PC-A command prompt: `ping 192.168.20.10` and `tracert 192.168.20.10`.

## Validation commands

RIP:
- `show ip protocols`
- `show ip route rip`
- `show ip route 192.168.20.0`
- `show ip interface brief`

OSPF:
- `show ip ospf neighbor`
- `show ip ospf interface brief` (where supported)
- `show ip route ospf`
- `show ip route 192.168.20.0`

## Failure
On R2 in each **separate project**, while the upper route is active:
```
enable
configure terminal
interface GigabitEthernet0/1
 shutdown
end
```

Once you finish collecting failure results, restore the link:
```
configure terminal
interface GigabitEthernet0/1
 no shutdown
end
```

Record pre-failure path, post-failure path, ICMP success/failures, and convergence evidence.
Use Packet Tracer Simulation Mode routing events and router table changes;
do not treat host wall-clock UI response time as precise router convergence time.
For cost demonstration, use the separate `configs/ospf/OPTIONAL_cost_demo.txt` commands only AFTER fair failure tests are complete.
