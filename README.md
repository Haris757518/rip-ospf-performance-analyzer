# Routing Protocol Performance Lab — VIT BITE305L (10-mark project)

**Project:** Performance Analysis of Distance Vector and Link State Routing Protocols Using Cisco Packet Tracer and a Python Streamlit Dashboard.

**Delivery status (2026-10-26):** `RIP_Experiment.pkt` and `OSPF_Experiment.pkt` are built and saved. Baseline and settled failover connectivity were verified for both protocols; each four-packet probe delivered 4/4 packets. OSPF restoration to the primary route was also verified. Both files were saved with the R2–R4 link restored. The dashboard loads five recorded observations from `data/measured_results.csv`; source console transcripts and scope limitations are in [the verification record](experiments/VERIFIED_RESULTS.md). All **33 automated software tests pass**. **Repeated benchmarking, convergence timings, the separate Cisco cost demonstration, and final report/presentation evidence remain unfinished.**

## Start in less than five steps
1. Extract the entire ZIP (do not run from inside the ZIP).
2. Install **Cisco Packet Tracer** and **Python 3.10+** if needed.
3. Open `TOPOLOGY_AND_PORTS.md`. Place five Cisco 2911 routers, two 2960 switches, and two PCs. Cable all ports using the exact port-to-port table.
4. For each router, copy the **entire** matching file from `configs/paste_ready` into the Cisco CLI; use RIP complete files in your RIP project, OSPF complete files in your OSPF project. Configure PCs per the topology guide. Save as `RIP_Experiment.pkt` and `OSPF_Experiment.pkt`.
5. On Windows, double-click **`START_DASHBOARD_WINDOWS.bat`** to install dashboard dependencies and launch Streamlit. Internet is needed once for package installation. Alternatively run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

Dashboard URL typically: **http://localhost:8501**.

## Files
- `configs/paste_ready/` — easiest Cisco CLI set; full base+protocol configuration for each of five routers, ready to paste.
- `configs/base/`, `configs/rip/`, `configs/ospf/` — independently inspectable settings.
- `TOPOLOGY_AND_PORTS.md` — exact physical links, IP addresses, host gateways, troubleshooting.
- `experiments/EXPERIMENT_PROTOCOL.md` — test setup, failover/recovery, fairness rules and measurement limitations.
- `dashboard/app.py`, `dashboard/core.py` — Streamlit dashboard, expected-path model and CSV validation.
- `data/results_template.csv` — unfilled, no invented data.
- `assets/network_topology.png` — diagram for report and demonstration.
- `tests/test_core.py` — expected route + data integrity unit tests.
- `docs/PROJECT_REPORT_DRAFT.docx` and `docs/PROJECT_REPORT_DRAFT.pdf` — report framework reflecting uploaded course template, with deliberately marked unexecuted sections.
- `docs/DEMO_PRESENTATION.pptx` — presentation outline for 10 marks.
- `docs/LITERATURE_REVIEW_15_PAPERS.csv` — structured literature review verification worksheet (15 entries not invented).

## Project idea in one sentence
Compare how RIP and OSPF select routes and recover from the same R2–R4 link failure, then explain verified observations using a dashboard.

## Experiment map
| Experiment | Description | Expected router path |
|---|---|---|
| Baseline | Both routes up, equal link costs | R1 → R2 → R4 |
| Failover | Shutdown R2 Gi0/1 (R2–R4) | R1 → R3 → R5 → R4, **after convergence** |
| Restoration | No shutdown on R2 Gi0/1 | R1 → R2 → R4, **after convergence** |
| OSPF cost demo | OSPF high top-link costs | OSPF: lower three-hop path; RIP unchanged on a separate baseline file |

**Model versus measurement:** The dashboard **computes illustrative shortest paths** and can graph recorded measurements. Cisco Workspace opens the saved `.pkt` experiments in the local Packet Tracer installation and exposes console evidence and configurations. This is a local file launcher, without live telemetry or device control. The animation does not determine convergence time. Enter only actual verified results. If no reliable timer exists, leave those cells empty.

## Testing
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests
```
Tests check the static shortest-path model, data validation, configuration consistency, and Streamlit startup, result filtering, and the Cisco launcher. They do not test Cisco firmware or `.pkt` configurations. Invalid numeric CSV values and missing columns are rejected before charting; blank numeric cells remain excluded from averages.

## References
- [Cisco RIP command reference](https://www.cisco.com/c/en/us/td/docs/ios/iproute_rip/command/reference/irr_book/irr_rip.html)
- [Cisco OSPF cost explanation](https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13689-17.html)
- [RIPv2 RFC 2453](https://www.rfc-editor.org/rfc/rfc2453)
- [OSPFv2 RFC 2328](https://www.rfc-editor.org/rfc/rfc2328)

## Checklist before final submission
- [ ] Working RIP Packet Tracer saved file
- [ ] Working OSPF Packet Tracer saved file
- [ ] Initial, failed, restored and cost-mode screenshots
- [ ] Repeated experimental results on real measurement basis
- [ ] Insert actual results and screenshots in report
- [ ] Verify and add 15 recent research papers (faculty template requirement)


## Visual dashboard

- **Routing Lab:** animated packets, protocol switch, link failure and recovery, experiment replay, speed and pause controls, router inspection, and an illustrative unequal-cost scenario.
- **Performance:** hover charts of actual packet delivery and hop counts, scenario filters, CSV import/export, and a convergence chart only when timed measurements exist.
- **Cisco Workspace:** open/download RIP and OSPF projects, browse console evidence, and view router configurations.

The Cisco launcher currently uses the installed Packet Tracer at D:/Cisco Packet Tracer 9.0.1/bin/PacketTracer.exe. Update that path in dashboard/app.py if the installation moves. Animations respect reduced-motion preferences.



## V2 integrated update — 2026-10-28

The supplied V2 engine is now integrated into the visual dashboard, alongside the saved Packet Tracer projects and five verified observations. Open **Failure Lab** first: play the forwarding trace, inspect a specific tick, then expand the per-router state. The playback slider is independent of the detailed inspection slider.

- **Failure Lab:** distributed RIP vectors and OSPF failure knowledge, transient forwarding walks, failed probes, source-route stabilization, update and recalculation events. Change assumptions in Model settings.
- **Scalability:** compare 5–36 routers under the same model parameters. Graphs describe different deterministic topologies; they do not isolate a causal effect of router count.
- **Decisions:** cost-8 upper links versus cost-1 lower links, plus comparisons under selected operating priorities. The original Routing Lab uses its separately labeled adjustable cost example.
- **Cisco Results:** existing recorded evidence loads automatically. Both original and V2 CSV schemas are accepted. V2 convergence_ms converts to seconds; capture_method maps to measurement_basis. Different network sizes and timing methods are kept separate. Blank measurements stay blank; invalid and duplicate trial rows are rejected.
- **Cisco Workspace:** original saved experiments, console evidence, and verified configurations are preserved. Local file launch is available; there is no live telemetry connection.

Engine source: dashboard/engine.py. UI: dashboard/labs.py. Measurement adapter: dashboard/measurements.py. The V2 experiment procedure is experiments/V2_EXPERIMENT_PROTOCOL.md; docs/UPGRADED_PROBLEM_AND_EXPERIMENT_DESIGN.md is a design template, not a completed empirical report. Existing actual findings remain in experiments/VERIFIED_RESULTS.md.

Model stabilization means the first final delivered source path retained through the remainder of the observation window, not global control-plane convergence. Ticks are not seconds. Update counts omit OSPF normal background traffic and cannot rank total real overhead. Repeated transition measurements and defensible Cisco timings still require collection.
