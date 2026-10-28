# Viva preparation – RIP vs OSPF project

## One-minute introduction
Our project compares distance-vector RIPv2 with link-state OSPFv2 using an identical five-router Cisco Packet Tracer topology. There are two possible paths from LAN A to LAN B. We observe normal routing, break the R2–R4 link, verify the alternative path, then restore connectivity. Separately, we change OSPF interface costs to illustrate how cost-based selection can prefer more hops. A Python Streamlit dashboard shows the topology, educational route calculations and graphs based on imported actual measurements.

## Faculty questions and short answers

**What problem are you solving?**
A fair, repeatable comparison of route selection and link-failure recovery, plus a visual way to explain the evidence.

**Why separate RIP and OSPF files?**
If both run at once, Cisco administrative distance and route selection can interfere with a fair comparison. One routing protocol is active per experimental configuration.

**Which algorithms?**
RIP is a distributed distance-vector protocol related to the Bellman–Ford principle and uses hop count. OSPF uses link-state advertisements and shortest-path-first (Dijkstra) with costs. Our Python model uses BFS for hop-minimal route illustration and Dijkstra for shortest-cost path. It **does not simulate protocol convergence timers**.

**What is a routing loop?**
A path that repeatedly forwards packets among routers without reaching the destination. RIP uses mechanisms such as split horizon/route poisoning to reduce routing loops and count-to-infinity effects.

**What is convergence?**
A state in which routers have updated routes consistent with current network connectivity. Our claim about time must be based on the recorded measurement method.

**What happens after R2–R4 fails?**
The planned alternate path is R1 → R3 → R5 → R4. It can be used once the routing protocol reconverges. The physical path exists even before convergence; an updated routing table is needed to use it reliably.

**Why is OSPF not always faster?**
Observed behavior depends on topology, timers, implementation, link failure detection and measurement method. Do not claim universal superiority based on a small teaching simulator experiment.

**What is the innovation?**
The project is a transparent teaching and measurement workflow connecting actual Packet Tracer configurations, repeatable controlled experiments and a dashboard that avoids fabricated measurements.

**Are the charts live?**
No. They show uploaded/entered Packet Tracer observations. The network topology is computed by a separate educational model, not by a direct Packet Tracer connection.

**What needs to be finished before submission?**
Save and test the two `.pkt` files in Packet Tracer, collect repeated results and screenshots, and fill the faculty-required 15-paper review with real verified references.
