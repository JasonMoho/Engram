# Memex-SR Extraction Node Audit: Generation 12

Source manifest: `deployments/memex-sr/manifests/paper_research_facts.jsonl`

This audit lists the non-evidence extraction nodes emitted by the first 10-paper paper-distillation batch. Evidence nodes are omitted from the main list because they are provenance support records rather than reusable concepts; the manifest contains all 61 evidence records.

## Totals

- Evidence: `61`
- Design principles: `29`
- Mechanisms: `30`
- Trade-offs: `24`
- Anti-patterns: `19`

## Nodes By Paper

### 1. A Case for Task Sampling based Learning for Cluster Job Scheduling

- Paper: `paper:nsdi:2022:a-case-for-task-sampling-based-learning-for-cluster-job-scheduling`
- Evidence records: `7`

Design principles:
- `p1`: Learn job runtime properties by sampling tasks of the job (learning in space) rather than relying solely on historical executions.
- `p2`: Select the prediction strategy based on measured variance: prefer spatial sampling when job-wise variance dominates and prefer history-based prediction when task-wise variance dominates.

Mechanisms:
- `m1` (design_pattern): SLearn pilot-task sampling
- `m2` (algorithm): History-based runtime prediction (e.g., 3Sigma)

Trade-offs:
- `t1`: Prediction accuracy vs. Runtime overhead / scheduling delay
- `t2`: Applicability to new/rare jobs vs. Operational overhead and simplicity

Anti-patterns:
- `a1`: Rely exclusively on history-based predictors in dynamic clusters
- `a2`: Use a fixed, tiny pilot-sample size without assessing task skew

### 2. Accelerating Collective Communication in Data Parallel Training across Deep Learning Frameworks

- Paper: `paper:nsdi:2022:accelerating-collective-communication-in-data-parallel-training-across-deep-lear`
- Evidence records: `5`

Design principles:
- `p1`: Cache and reuse coordination metadata collected at runtime to avoid repeated centralized orchestration across iterations.
- `p2`: Expose explicit grouping of collective operations to let users control tensor fusion and communication buffer sizing.
- `p3`: Prefer tight integration with lower-level data-plane collective implementations (e.g., NCCL tree-based algorithms) while addressing control-plane scalability separately.

Mechanisms:
- `m1` (architecture): Response cache + decentralized orchestration with bitvector intersection
- `m2` (design_pattern): User-visible grouping for collective operations (explicit tensor fusion)
- `m3` (protocol): Use high-performance data-plane collectives (e.g., NCCL tree-based AllReduce) while decoupling control-plane orchestration

Trade-offs:
- `t1`: Simplicity of a centralized coordinator-worker control plane vs. Scalability and low per-iteration overhead
- `t2`: Automatic tensor fusion for ease of use vs. Manual grouping for optimal buffer sizing
- `t3`: Portability across frameworks (framework-agnostic design) vs. Access to model internals for optimal scheduling (framework-native design)

Anti-patterns:
- `a1`: Executing coordinator-worker control-plane orchestration on every iteration without caching
- `a2`: Relying solely on automatic tensor-fusion heuristics without providing grouping controls

### 3. An edge-queued datagram service for all datacenter traffic

- Paper: `paper:nsdi:2022:an-edge-queued-datagram-service-for-all-datacenter-traffic`
- Evidence records: `5`

Design principles:
- `p1`: Move queuing out of the network core and into sender-side queues (edge-queuing).
- `p2`: Use a receiver-driven credit control loop to clock edge queues into the network.
- `p3`: Expose virtual interface queues (EQIFs) per sender and receiver to implement different queuing disciplines and sharing policies.

Mechanisms:
- `m1` (protocol): EQDS UDP tunnel with NDP-derived receiver-driven control loop
- `m2` (architecture): EQIF sender-side queues and receiver-side reorder buffer
- `m3` (algorithm): PULL-based crediting with packet trimming
- `m4` (design_pattern): Packet spraying (per-packet ECMP) with small switch queues

Trade-offs:
- `t1`: Minimize in-network queuing latency and enable coexistence of dissimilar transports vs. Keep host/NIC complexity and buffering low
- `t2`: Maximize network utilization via packet spraying vs. Maintain in-order delivery semantics expected by legacy transports
- `t3`: Deploy EQDS as a soft-state UDP tunnel for compatibility and incremental deployment vs. Avoid overhead and complexity of managing soft-state tunnels at scale

Anti-patterns:
- `a1`: Tunnel all datacenter traffic over a single new receiver-driven transport in the network core without moving queueing to the edge.
- `a2`: Embed full transport state and heterogenous transport logic into NICs/switch hardware as a deployment shortcut.

### 4. Aquila: A unified, low-latency fabric for datacenter networks

- Paper: `paper:nsdi:2022:aquila-a-unified-low-latency-fabric-for-datacenter-networks`
- Evidence records: `7`

Design principles:
- `p1`: Treat a Clique as the unit of deployment and homogeneity so intra-Clique innovations can provide predictable, low-latency primitives without changing inter-Clique IP semantics.
- `p2`: Vertically integrate NIC and ToR switch functionality into a single, replicated silicon component (TiN) to reduce development cost and streamline management.
- `p3`: Design the fabric around small cells, shallow buffering, link-level flow-control, and end-to-end admission control so latency is bounded even under contention.

Mechanisms:
- `m1` (protocol): GNet (cell-based Layer-2 protocol)
- `m2` (architecture): ToR-in-NIC (TiN) combined silicon
- `m3` (protocol): End-to-end solicitation / admission control per packet
- `m4` (protocol): 1RMA (co-designed remote memory access over GNet)

Trade-offs:
- `t1`: Minimize tail latency via shallow buffering and flow-control vs. Maintain safety and stability (avoid tree saturation and uncontrolled congestion)
- `t2`: Reduce hardware development and inventory cost by unifying NIC and ToR into TiN vs. Provide per-host dedicated bandwidth and scalability
- `t3`: Enable radical internal Layer-2 redesigns for performance vs. Maintain backward compatibility and manageability across the datacenter

Anti-patterns:
- `a1`: Apply shallow buffering or link-level flow-control in isolation without admission control or matched design changes.
- `a2`: Deploying separate purpose-built networks (a ‘bag-on-the-side’) for niche low-latency workloads while leaving the main datacenter network unchanged.

### 5. Automated Verification of Network Function Binaries

- Paper: `paper:nsdi:2022:automated-verification-of-network-function-binaries`
- Evidence records: `5`

Design principles:
- `p1`: Use a universal, implementation-agnostic abstract type (ghost maps) to represent data-structure state in specifications and contracts.
- `p2`: Leverage well-defined environment interactions as the primary interface for inferring types and control flow when source/debug info is unavailable.
- `p3`: Express data-structure contracts separately (once per DS implementation) so NF verification composes concrete binaries with abstract contracts.

Mechanisms:
- `m1` (data_structure): Ghost maps (map-based DS abstraction)
- `m2` (algorithm): Environment-driven type and control-flow inference
- `m3` (architecture): Klint verification architecture

Trade-offs:
- `t1`: Support arbitrary concrete data-structure implementations and languages vs. Avoid assuming or verifying the correctness of those data-structures
- `t2`: Precisely model NF environment to enable binary verification vs. Minimize manual effort to build environment models

Anti-patterns:
- `a1`: Require source code or specific in-language data-structure idioms to enable verification
- `a2`: Attempt to model a full general-purpose OS environment to extract types/control flow for arbitrary binaries

### 6. Backdraft: a Lossless Virtual Switch that Prevents the Slow Receiver Problem

- Paper: `paper:nsdi:2022:backdraft-a-lossless-virtual-switch-that-prevents-the-slow-receiver-problem`
- Evidence records: `6`

Design principles:
- `p1`: Avoid HOL blocking by providing per-flow isolation at the vswitch (one queue per flow).
- `p2`: Separate control/notification (doorbell) and data paths to minimize CPU scanning/overhead for many queues.
- `p3`: Leverage abundant end-host memory with dynamic allocation (reclaim and resize) to make per-flow queuing feasible.

Mechanisms:
- `m1` (data_structure): Dynamic Per-Flow Queuing (DPFQ)
- `m2` (design_pattern): Doorbell Queues (separate notification queue)
- `m3` (protocol): Vswitch Overlay Backpressure Network

Trade-offs:
- `t1`: Minimize head-of-line blocking between flows vs. Minimize memory footprint of the vswitch
- `t2`: Provide fine-grained per-flow queues vs. Keep CPU overhead low
- `t3`: Prevent packet loss via backpressure vs. Avoid congestion spreading into the network core

Anti-patterns:
- `a1`: Apply hardware-style bandwidth reservation/rate-limiting assuming deterministic line-rate to a vswitch
- `a2`: Use hardware PAUSE/PFC-style backpressure directly from vswitches to upstream switches

### 7. Backpressure Flow Control

- Paper: `paper:nsdi:2022:backpressure-flow-control`
- Evidence records: `6`

Design principles:
- `p1`: Prefer per-hop, per-flow flow control implemented at switches (hop-by-hop backpressure) rather than relying solely on end-to-end feedback when low tail latency and fast reaction are required.
- `p2`: Bound per-flow state by maintaining state only for 'active' flows (those with queued packets) and size flow tables proportional to the number of physical queues.
- `p3`: Dynamically assign flows to empty queues when possible and use queue-level pause/resume (backpressure) with small occupancy thresholds to limit buffering.

Mechanisms:
- `m1` (protocol): Backpressure Flow Control (BFC) protocol
- `m2` (data_structure): Dynamic queue assignment via hashed flow table + empty-queue bitmap
- `m3` (algorithm): Queue-level pause/resume backpressure with DRR scheduling

Trade-offs:
- `t1`: Minimize tail latency and fast reaction to congestion vs. Minimize per-switch memory/state and number of physical queues
- `t2`: Minimize buffering (small per-flow queues and aggressive pause thresholds) vs. Maintain high link utilization under bursty traffic

Anti-patterns:
- `a1`: Hashing all flows to a small fixed set of FIFO queues without dynamic binding
- `a2`: Relying solely on end-to-end RTT-delayed congestion control in high-bandwidth, bursty datacenter networks

### 8. Bluebird: High-performance SDN for Bare-metal Cloud Services

- Paper: `paper:nsdi:2022:bluebird-high-performance-sdn-for-bare-metal-cloud-services`
- Evidence records: `8`

Design principles:
- `p1`: Implement the data plane on programmable ToR ASICs to achieve hardware-like performance (line-rate throughput and sub-microsecond latency) for bare-metal workloads.
- `p2`: Use a ToR bump-in-the-wire architecture and per-customer VRFs to decouple SDN functionality from bare-metal hosts and provide strong tenant isolation.
- `p3`: Mitigate limited on-chip route-table capacity by augmenting the ToR with an onboard route cache and a control-plane caching strategy.

Mechanisms:
- `m1` (data_structure): Onboard route cache for ToR switches
- `m2` (architecture): Per-customer VRF with VXLAN static CA-to-PA routes and P4-based encapsulation
- `m3` (architecture): P4-programmable ASIC data plane

Trade-offs:
- `t1`: Achieve hardware-like, low-latency, high-throughput forwarding on the ToR vs. Support large numbers of tenant routes/hosts given limited on-chip route memory
- `t2`: Use smartNIC or host-based SDN to offload per-flow processing to host-adjacent devices vs. Maintain a host-agnostic, easily-deployable solution for bare-metal tenants

Anti-patterns:
- `a1`: Building bare-metal SDN by relying on host-based vSwitches or smartNIC-host integration (i.e., treating bare-metal like VM hosts).

### 9. Buffer-based End-to-end Request Event Monitoring in the Cloud

- Paper: `paper:nsdi:2022:buffer-based-end-to-end-request-event-monitoring-in-the-cloud`
- Evidence records: `6`

Design principles:
- `p1`: Model the end-to-end request datapath as a buffer chain and treat RLA root causes as buffer-related abnormal events.
- `p2`: Define a uniform buffer event taxonomy based on buffer properties to enable consistent semantics across diverse buffer implementations.
- `p3`: Ensure captured network events carry request-level identifiers by injecting request semantics into packets and performing extraction in programmable data plane/hardware.

Mechanisms:
- `m1` (architecture): Buffer-event modeling and monitoring
- `m2` (design_pattern): Request-level semantic injection and hardware extraction
- `m3` (data_structure): Buffer event library mapped from buffer properties

Trade-offs:
- `t1`: Maximize coverage of RLA root causes vs. Keep monitoring overhead (bandwidth, CPU, throughput) minimal
- `t2`: Implement request semantic extraction in software (end-host stack) vs. Offload semantic extraction to SmartNIC/hardware

Anti-patterns:
- `a1`: Relying on separate application tracing and network flow monitors and correlating them by coarse-grained time correlation
- `a2`: Inject request-level semantics in the end-host network stack (software strawman) for RTC workloads

### 10. C2DN: How to Harness Erasure Codes at the Edge for Efficient Content Delivery

- Paper: `paper:nsdi:2022:c2dn-how-to-harness-erasure-codes-at-the-edge-for-efficient-content-delivery`
- Evidence records: `6`

Design principles:
- `p1`: Use erasure coding for large cached objects at the CDN edge to improve space-efficiency and availability while reducing byte miss ratio.
- `p2`: Exploit parity chunks as flexible placement tokens to rebalance write and eviction load across servers, reducing write imbalance and eviction-induced misses.
- `p3`: Adopt a hybrid redundancy strategy: replicate small objects and erasure-code large objects to balance performance overheads and space efficiency.

Mechanisms:
- `m1` (algorithm): Parity rebalance via Max Flow assignment
- `m2` (architecture): In-cluster selective coding with sub-chunk streaming

Trade-offs:
- `t1`: Minimize storage overhead (use erasure coding) vs. Minimize per-request CPU/IO overhead and origin traffic
- `t2`: Achieve near-perfect write/eviction balance via Max Flow parity placement vs. Keep computational cost and mapping freshness low

Anti-patterns:
- `a1`: Replicate every object across multiple servers within a cluster to achieve availability
- `a2`: Perform erasure coding at origins to avoid CDN-side complexity

## Quality Read

- Strongest signal: named mechanisms and trade-offs. These are usually concrete and paper-specific, e.g. BFC protocol, EQDS receiver-driven control, Dynamic Per-Flow Queuing, parity rebalance via max-flow.
- Mixed signal: design principles. Some are genuinely reusable, while some are paper-specific design choices phrased as principles.
- Weakest signal: anti-patterns. Many are plausible inversions of the paper contribution rather than explicitly established community anti-patterns.
- Main missing guardrail: exact source spans/quotes. The nodes point to chunks, but they do not yet carry precise spans or short evidence quotes.
- Main missing synthesis step: deduplication and canonicalization across papers. The batch currently emits per-paper nodes, not merged textbook concepts.
