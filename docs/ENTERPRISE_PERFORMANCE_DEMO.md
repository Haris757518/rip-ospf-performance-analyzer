# Enterprise WAN performance analysis

The default Enterprise WAN tab contains 12 routers and 18 redundant links. It is an abstract routing experiment, not a new verified Packet Tracer file. The existing RIP_Experiment.pkt and OSPF_Experiment.pkt remain the verified five-router testbed.

## Why these protocols can differ

HQ R1 reaches data center R12 through a short legacy WAN or a longer core path. Branch gateways, cross-links and a DR transit route supply alternate forwarding choices. Site names represent logical roles, not measured hardware characteristics.

- RIP baseline: R1 → R2 → R12, two hops, configured path cost 24.
- OSPF baseline: R1 → R3 → R5 → R8 → R12, four hops, configured path cost 8.
- These are configured costs. They do not establish latency, bandwidth, throughput or monetary cost.

## Demonstration

1. Open Enterprise WAN with WAN costs selected. Both routes appear on the same diagram. Hover over links to inspect costs; click routers for site roles and neighbors. Use the route selector if paths overlap.
2. Fail R2–R12 and press Play failure. RIP loses its selected legacy route while OSPF's selected core route survives. Explain that different baseline routes make their exposure different; this alone is not proof of generally faster recovery.
3. Choose Equal costs and keep R2–R12 as the failed link. Both protocols start on the same path. Compare failed probes and stabilization through the identical observation window.
4. Try R8–R12, R5–R8 and R1–R3. A protocol is not guaranteed to win every scenario. Source route stabilization is not global protocol convergence.
5. Show the service availability and cumulative update plots. Timing settings are in Failure Lab → Model settings and apply to the enterprise experiment too. Each trace contains one probe per tick, including tick zero; a 48-tick horizon has 49 probes.
6. Open Scalability to compare increasing network sizes. These use separately generated ring-and-shortcut topologies, not copies of the 12-router enterprise topology.
7. Open Cisco Results to distinguish recorded five-router observations from the enterprise model. No enterprise measurements or real convergence timings have been fabricated.

## Why the title is performance analysis

The project compares route efficiency (hops and configured cost), service continuity (transient failed probes), source-path stabilization, control activity (modeled transmissions and calculations), and sensitivity to topology size and timers. It combines reproducible algorithm experiments with separately documented Cisco evidence. It does not claim a complete real-device benchmark. Normal OSPF Hellos, acknowledgements and retransmissions are omitted, so event counts cannot rank total wire overhead or CPU consumption.

## Building the enterprise experiment in Cisco

Use ENTERPRISE_WAN_LINK_PLAN.csv for the 18 /30 WAN subnets and endpoint addresses. Build the same links in two independent saves, one RIP v2 and one OSPF area 0. Use devices/modules supporting the required number of routed Ethernet ports: R5, R8 and R9 require four; verify all degrees against the link plan. Interface names depend on the chosen Packet Tracer device; map physical ports before pasting configuration.

Give each router loopback 172.16.<router-number>.1/32; use R1's loopback as source and R12's as destination for routing-only tests. Advertise all 10.20.0.0 WAN subnets and loopbacks with RIP v2 (no auto-summary), or OSPF area 0. Apply each link's configured OSPF cost on both endpoints for WAN-cost tests; reset every cost to 1 for matched recovery tests. RIP ignores OSPF cost settings. This is a single-area comparison; the model does not emulate OSPF areas.

Capture baseline routes and probes, fail the planned physical interface, record equivalent transition windows, and restore before each repeated trial. Collect at least three trials per protocol and declare the clock/capture method. Import using router_count=12 in the V2 measurement CSV. Until built and tested in Cisco, the enterprise scenario remains model-only.

The modeled route cost ends at R12. A Cisco route to its loopback may include an additional destination interface cost; report the actual routing-table metric with that distinction.
