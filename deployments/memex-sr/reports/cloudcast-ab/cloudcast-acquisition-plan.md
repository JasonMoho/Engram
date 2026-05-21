# Cloudcast Acquisition Plan

Generated: `2026-05-20T16:09:23+00:00`
Source manifest: `deployments/memex-sr/fixtures/cloudcast_sources.yaml`

## Summary

- Non-holdout records: `29`
- Total records in plan: `29`
- Actions: `{"fetch_open": 12, "queue_mit_manual": 8, "skip_metadata_only": 5, "use_local_file": 4}`
- Categories: `{"algorithmic_foundation": 6, "benchmark": 4, "cloud_economics": 3, "direct_system": 12, "implementation_guidance": 4}`
- Access basis: `{"licensed_local": 1, "metadata_only": 5, "mit_authenticated": 7, "open": 12, "operator_supplied": 4}`

## Records

| Source | Tier | Category | Access | Action | State | Target |
|:--|--:|:--|:--|:--|:--|:--|
| `cloudcast:fair-task-prompt` | 0 | benchmark | operator_supplied | use_local_file | local_available | `SystemBench/ADRS/cloudcast/deepagents_files/task_prompt_direction.txt` |
| `cloudcast:simulator` | 0 | benchmark | operator_supplied | use_local_file | local_available | `SystemBench/ADRS/cloudcast/simulator.py` |
| `cloudcast:evaluator` | 0 | benchmark | operator_supplied | use_local_file | local_available | `SystemBench/ADRS/cloudcast/evaluator.py` |
| `cloudcast:initial-program` | 0 | benchmark | operator_supplied | use_local_file | local_available | `SystemBench/ADRS/cloudcast/initial_program.py` |
| `systems:skyplane` | 1 | direct_system | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/systems_skyplane/source.html` |
| `systems:cloudmpcast` | 1 | direct_system | metadata_only | skip_metadata_only | landing_only | `deployments/memex-sr/.cache/cloudcast_sources/systems_cloudmpcast/source.html` |
| `systems:spanstore` | 1 | direct_system | mit_authenticated | queue_mit_manual | needs_mit_operator | `deployments/memex-sr/.cache/cloudcast_sources/systems_spanstore/source.html` |
| `systems:b4` | 1 | direct_system | mit_authenticated | queue_mit_manual | needs_mit_operator | `deployments/memex-sr/.cache/cloudcast_sources/systems_b4/source.html` |
| `systems:swan` | 1 | direct_system | mit_authenticated | queue_mit_manual | needs_mit_operator | `deployments/memex-sr/.cache/cloudcast_sources/systems_swan/source.html` |
| `systems:ron` | 1 | direct_system | mit_authenticated | queue_mit_manual | needs_mit_operator | `deployments/memex-sr/.cache/cloudcast_sources/systems_ron/source.html` |
| `systems:end-system-multicast` | 1 | direct_system | metadata_only | skip_metadata_only | landing_only | `deployments/memex-sr/.cache/cloudcast_sources/systems_end-system-multicast/source.html` |
| `systems:splitstream` | 1 | direct_system | mit_authenticated | queue_mit_manual | needs_mit_operator | `deployments/memex-sr/.cache/cloudcast_sources/systems_splitstream/source.html` |
| `systems:bullet` | 1 | direct_system | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/systems_bullet/source.pdf` |
| `systems:bittorrent` | 1 | direct_system | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/systems_bittorrent/source.pdf` |
| `systems:kraken` | 1 | direct_system | metadata_only | skip_metadata_only | landing_only | `deployments/memex-sr/.cache/cloudcast_sources/systems_kraken/source.html` |
| `systems:netstitcher` | 1 | direct_system | metadata_only | skip_metadata_only | landing_only | `deployments/memex-sr/.cache/cloudcast_sources/systems_netstitcher/source.html` |
| `algorithms:directed-steiner-charikar` | 2 | algorithmic_foundation | mit_authenticated | queue_mit_manual | needs_mit_operator | `deployments/memex-sr/.cache/cloudcast_sources/algorithms_directed-steiner-charikar/source.html` |
| `algorithms:steiner-tree-survey` | 2 | algorithmic_foundation | mit_authenticated | queue_mit_manual | needs_mit_operator | `deployments/memex-sr/.cache/cloudcast_sources/algorithms_steiner-tree-survey/source.html` |
| `algorithms:network-flows-book` | 2 | algorithmic_foundation | licensed_local | queue_mit_manual | needs_mit_operator | `deployments/memex-sr/.cache/cloudcast_sources/algorithms_network-flows-book/source.html` |
| `algorithms:multicommodity-flow-survey` | 2 | algorithmic_foundation | metadata_only | skip_metadata_only | landing_only | `deployments/memex-sr/.cache/cloudcast_sources/algorithms_multicommodity-flow-survey/source.html` |
| `algorithms:column-generation` | 2 | algorithmic_foundation | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/algorithms_column-generation/source.html` |
| `algorithms:benders-decomposition` | 2 | algorithmic_foundation | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/algorithms_benders-decomposition/source.html` |
| `implementation:pulp` | 3 | implementation_guidance | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/implementation_pulp/source.html` |
| `implementation:networkx-shortest-paths` | 3 | implementation_guidance | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/implementation_networkx-shortest-paths/source.html` |
| `implementation:or-tools-min-cost-flow` | 3 | implementation_guidance | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/implementation_or-tools-min-cost-flow/source.html` |
| `implementation:scipbook` | 3 | implementation_guidance | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/implementation_scipbook/source.html` |
| `cloud-economics:aws-data-transfer` | 4 | cloud_economics | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/cloud-economics_aws-data-transfer/source.html` |
| `cloud-economics:gcp-network-pricing` | 4 | cloud_economics | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/cloud-economics_gcp-network-pricing/source.html` |
| `cloud-economics:azure-bandwidth` | 4 | cloud_economics | open | fetch_open | planned_open_fetch | `deployments/memex-sr/.cache/cloudcast_sources/cloud-economics_azure-bandwidth/source.html` |

This is a dry-run plan. It does not download sources. `queue_mit_manual` records require an operator to retrieve material through approved MIT library or browser workflows and then register local files with provenance.
