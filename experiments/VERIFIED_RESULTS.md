# Packet Tracer verification record

These observations came from the running Cisco Packet Tracer project. Original console text is retained in `evidence/`; some transcripts include earlier command history. Use the final relevant command block in each named transcript.

| Protocol | State | Verified route | Router-to-router hops | Destination route metric | ICMP received/sent |
|---|---|---|---:|---:|---:|
| RIP | Baseline, existing user run | R1 → R2 → R4 | 2 | 2 | 4/4 |
| RIP | R2 Gi0/1 shut down, settled | R1 → R3 → R5 → R4 | 3 | 3 | 4/4 |
| OSPF | Baseline | R1 → R2 → R4 | 2 | 3 | 4/4 |
| OSPF | R2 Gi0/1 shut down, settled | R1 → R3 → R5 → R4 | 3 | 4 | 4/4 |
| OSPF | Link restored | R1 → R2 → R4 | 2 | 3 | Not collected |

R1's OSPF neighbor table showed R2 and R3 in FULL/BDR state. Both failover traceroutes traversed 192.168.10.1, 10.0.13.2, 10.0.35.2, 10.0.45.2, and the destination PC 192.168.20.10.

## Saved projects

- `RIP_Experiment.pkt`: RIP configuration; R2–R4 restored before saving.
- `OSPF_Experiment.pkt`: OSPF configuration with RIP removed on every router; R2–R4 restored and primary route verified before saving.
- `data/measured_results.csv`: recorded observations loaded by the dashboard by default.

## What these checks establish

Both protocols provide end-to-end reachability after settling and select a working alternative path after the same primary-link failure. The four-packet probes all delivered 4/4 packets **after routes settled**. These are single verification runs, not repeated benchmarks or measurements of packet loss during the interruption.

OSPF's subnet metric includes the R4 outgoing LAN interface: the baseline metric is 3 and the backup metric is 4. The dashboard's educational graph ends at R4 and therefore displays costs 2 and 3 for the corresponding equal-cost paths.

## Still required for a complete academic comparison

- Three independently reset trials per protocol and condition.
- Consistently defined and evidenced failure/restoration start and end timestamps before reporting convergence seconds.
- Matched ICMP observation windows spanning the outage if comparing interruption loss.
- Separate OSPF cost demonstration; no cost overrides were applied during these fair failover checks.
- Screenshots and findings inserted into the report/presentation drafts, and verified literature review.

No conclusion about which protocol converges faster follows from these checks. Convergence cells remain blank intentionally.
