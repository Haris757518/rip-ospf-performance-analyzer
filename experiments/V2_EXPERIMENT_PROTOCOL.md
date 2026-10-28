# Repeatable Cisco Packet Tracer experiment procedure

## Project and fairness statement
Two separate Packet Tracer files must use identical cables, hardware, IPv4 subnetting and baseline router link costs. **Never** compare protocol timings from different timing bases. RIP and OSPF are configured in separate files. **Do not enable the optional OSPF cost overrides during failover measurements.**

### Records to collect

| Column | What goes here | Example of evidence |
|---|---|---|
| protocol | `RIP` or `OSPF` | `show ip protocols` |
| experiment | `baseline`, `failover`, `recovery`, `cost_demo` | Label your run |
| trial | 1, 2, 3... | Reproducible run identifier |
| measurement_basis | `Packet Tracer simulated time`, `Manual stopwatch`, etc. | Record precise definition in notebook |
| convergence_s | seconds from defined failure/restoration event to confirmed usable new route | Simulation timeline + route verification (optional, leave blank if unsupported) |
| sent_packets, received_packets | count ICMP echoes for identical observation windows | Ping/Simulation capture |
| route_hops | **router-to-router** hops (R1→R2→R4 = 2) | Router routing table + tracert |
| route_path | observed router sequence | `R1 -> R3 -> R5 -> R4` |
| evidence_note | filename of real screenshot and notes | `screenshots/RIP_failover_trial1.png` |

### Stage A — Network construction
1. Build the exact topology in `TOPOLOGY_AND_PORTS.md`.
2. Configure PC addresses from the guide. Paste matching `configs/base` file into each router CLI.
3. Verify interface states (`show ip interface brief`). Fix all down/down links before continuing.
4. Save `Common_Base.pkt` as the interface-only topology.
5. Save two copies: `RIP_Experiment.pkt` and `OSPF_Experiment.pkt`.
6. In the first project, paste `configs/rip` into matching routers. In the second, paste `configs/ospf`. Verify the correct protocol.
7. Wait for routing to stabilize. Ping the opposite PC and inspect R1 route `show ip route 192.168.20.0`.

### Stage B — Baseline test
1. Capture a screenshot of the topology and R1 route table for each protocol.
2. From PC-A: `tracert 192.168.20.10` and `ping 192.168.20.10`.
3. Record route, router hops, packets sent/received, timestamps/method and screenshots. A single ping may fail due to ARP before the path settles; identify warm-up pings separately.

### Stage C — Controlled link outage
1. Use a **fresh stabilized** file for each run, starting with both inter-router paths up.
2. On **R2 Gi0/1**, issue `shutdown` to break R2–R4, not a whole router power-off.
3. If using Simulation Mode, retain its event list and record the source of any timing values. Observe routing-table update and check delivery after recovery.
4. Confirm new R1 path via R3 and R5, then record screenshot and metrics.
5. Repeat three times per protocol, restoring or reopening a fresh saved baseline after each run.

### Stage D — Link restoration
1. Starting from a stable failed-link state, issue `no shutdown` on R2 Gi0/1.
2. Check when the network returns to the preferred upper path; record route and evidence.
3. Repeat three times with equivalent starting states.

### Stage E — OSPF metric demonstration (NOT part of fair failover data)
1. Duplicate OSPF baseline into `OSPF_Cost_Demo.pkt`.
2. Apply per-router commands in `configs/ospf/OPTIONAL_cost_demo.txt`.
3. Upper link interface cost 100 each, lower link interface cost 10 each. `show ip route 192.168.20.0` should indicate the lower path from R1.
4. Use `show ip ospf interface` (where supported) to confirm actual costs.
5. Compare to RIP's unchanged hop-based upper path; report this as an **illustration of metrics**, not as a recovery benchmark.

## Convergence measurement limitations
- Define a start event and an end event **before** measuring. Possible end is first verified stable usable backup route in R1 routing table with successful end-to-end forwarding; do not substitute the moment you clicked Shutdown as a simulated timestamp.
- Packet Tracer event time does not correspond to hardware forwarding latency. The simulator may not offer sufficiently fine-grained/reliable timestamps for rigorous end-to-end convergence measurement. **If you cannot document both timestamps, leave convergence_s blank** and report comparative state transitions qualitatively.
- Avoid using `ping` output alone to claim control-plane convergence.
- Same tests and same timing basis for both protocols; match observation windows for packet delivery.
- Do not calculate CPU usage or throughput unless explicitly collected with a valid tool and method.

## Verification CLI
```
show ip interface brief
show ip protocols
show ip route
show ip route 192.168.20.0
show ip route rip
show ip route ospf
show ip ospf neighbor
```

## Required evidence before submission
- Screenshots from BOTH `.pkt` files of initial topology and stable initial routing tables.
- Confirmed link outage and resulting rerouted R1 table for BOTH protocols.
- Confirmed restored state for BOTH protocols.
- Cost-example verification screenshot in OSPF file.
- Original measured CSV with no fabricated values, clearly defined method and trials.
