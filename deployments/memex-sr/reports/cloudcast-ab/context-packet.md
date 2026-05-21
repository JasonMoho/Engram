# Research Context Packet

**Problem:** cloudcast
**Domain:** networking
**Topics:** multicast, routing, traffic-engineering, cost-aware-routing
**Generation:** 4

## Problem Class

Wide-area network capacity planning and load balancing — cloudcast targets the cost-tuned routing / multicast selection family (objective: minimize $/byte under throughput + jitter SLOs). Adjacent problem families: BGP route reflector design, anycast prefix steering, MPLS TE path computation.

## Design Principles

- (none indexed for these topics in this generation)

## Mechanisms To Try

- (none indexed for these topics in this generation)

## Trade-Off Map

- (none indexed for these topics in this generation)

## Experiment Advice

- Metrics to inspect: per-flow $/byte, p99 latency, jitter, link utilization variance.
- Stress cases to add: bursty traffic (Pareto-distributed flow sizes); link failures mid-run; asymmetric capacity.
- Ablations to run: hold the topology fixed and vary the objective weighting (latency vs cost); hold the objective fixed and vary the multicast tree algorithm.

## Anti-Patterns

- (none indexed for these topics in this generation)

## Evidence Index

- (no evidence nodes match these topics in this generation)
