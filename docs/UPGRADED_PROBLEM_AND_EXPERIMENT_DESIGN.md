# Revised Course Project: Problem, Methodology and Expected Evidence

## Title
Performance Analysis of Distance Vector and Link State Routing Protocols Using Failure Recovery, Routing Overhead and Scalability Experiments

## Problem statement
Routing-protocol choices affect the service continuity and route quality of a dynamic computer network. Packet delivery under normal, stable conditions is not enough to evaluate a routing protocol: two protocols can both achieve 100% delivery after recovery while exhibiting different temporary disruptions, route selection, control-plane communication and scalability characteristics. This project creates a repeatable testbed for RIP v2 and OSPF, compares the reactions of each protocol to identical disturbances, and provides criteria for selecting a protocol based on documented conditions.

## Research questions
- RQ1: Which protocol reestablishes stable source-to-destination connectivity sooner under a matched link failure, within a stated test method?
- RQ2: How do routing-update events and transient failed probes vary under the protocol models?
- RQ3: How does network size influence the modeled control-event count, routing recalculations and recovery behavior?
- RQ4: How can hop count and configured interface cost lead to different path choices?

## Independent variables
Protocol (RIP v2 / OSPF); failure scenario; link costs (kept equal for recovery comparison); network size (for MODEL-ONLY scalability); periodic and triggered model timers.

## Dependent variables
Recovered route, attempted forwarding path, probe delivery during transition, model convergence ticks, model control-message transmissions, model route recalculation events, and (when genuinely recorded) Packet Tracer success rate and documented timing.

## Controls
Identical topology, interface addresses, traffic endpoints, failed link, starting converged state, probe schedule and observation window for both protocols. Recover baseline between trials. Run at least three trials when collecting measured evidence.

## Architecture
```
 Cisco Packet Tracer (5 routers, RIP v2 / OSPF)
           | manual observations + protocol commands
           v
 Validated measured CSV ------------> Measured evidence dashboard

 Abstract routing model (per-router DV or LSDB states)
           | discrete-event trace and scenario generator
           v
 Failure lab -> scale lab -> qualified routing decision helper
```

## Implementation mechanics
1. Create identical network topologies; configure IPv4 interfaces, RIPv2 or OSPF area 0. Save separate Packet Tracer files.
2. Verify connectivity; inspect `show ip route`, `show ip protocols`, `tracert`.
3. Shut R2 G0/1, observe alternative route on both protocols, record the timing method; repeat from equivalent baselines.
4. Model: initialize all routers to converged state, then remove R2–R4 at tick zero. Endpoints detect immediately. In RIP, use distributed hop-count distance vectors and neighbor advertisements; in OSPF, use link-state announcements and shortest-path recalculations. Abstract tick != real time.
5. Track one forwarding probe per tick. Mark route stable at the first tick when the final delivered path is maintained for the remainder of the observation window.
6. Repeat model over increasingly large ring-plus-shortcut graphs; compare counts but discuss different topologies and omitted real-world costs.
7. Upload collected Cisco trial rows to make *measured* plots separate from *model* plots.

## Primary results table (to fill from real evidence)
| Scenario | Protocol | Repeats | Route before/after | Delivered/sent | Verified convergence time (optional) | Evidence |
|---|---|---:|---|---:|---|---|
| Normal | RIP | [pending] | [pending] | [pending] | n/a | screenshots |
| Normal | OSPF | [pending] | [pending] | [pending] | n/a | screenshots |
| R2–R4 failed | RIP | [pending] | [pending] | [pending] | [pending/unknown] | screenshots + traces |
| R2–R4 failed | OSPF | [pending] | [pending] | [pending] | [pending/unknown] | screenshots + traces |
| Restored | RIP | [pending] | [pending] | [pending] | [pending/unknown] | screenshots |
| Restored | OSPF | [pending] | [pending] | [pending] | [pending/unknown] | screenshots |

## Honest limitations
- This dashboard is an educational approximation, not a Cisco IOS protocol emulator. Do not call its ticks milliseconds or seconds.
- OSPF modeled update counts do not include Hello, acknowledgements or full adjacency traffic; RIP triggered behavior is simplified; do not compare modeled counts as exact total wire overhead.
- Not implemented: a socket-based live link to Packet Tracer, full protocol packet capture, CPU metrics, real throughput or hardware measurements.
- The `docs/` file is NOT a finished empirical report and provides no fake measurements.

## Conclusion structure (write only after real tests)
State how observed paths differed, whether evidence demonstrates recovery-time differences, what model assumptions explain the behavior, and what protocol selection is justified for the tested topology. Explicitly separate model claims from Packet Tracer claims.
