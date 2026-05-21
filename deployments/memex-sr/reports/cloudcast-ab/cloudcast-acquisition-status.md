# Cloudcast Acquisition Status

Generated: `2026-05-20T16:24:28+00:00`

## Summary

- Records: `29`
- Available local files: `16`
- States: `{"cached": 10, "fetched": 2, "landing_only": 5, "local_available": 4, "needs_mit_operator": 8}`

## Records

| Source | Action | State | Available | Bytes | Local file |
|:--|:--|:--|:--:|--:|:--|
| `cloudcast:fair-task-prompt` | use_local_file | local_available | yes | 10637 | `SystemBench/ADRS/cloudcast/deepagents_files/task_prompt_direction.txt` |
| `cloudcast:simulator` | use_local_file | local_available | yes | 23442 | `SystemBench/ADRS/cloudcast/simulator.py` |
| `cloudcast:evaluator` | use_local_file | local_available | yes | 25980 | `SystemBench/ADRS/cloudcast/evaluator.py` |
| `cloudcast:initial-program` | use_local_file | local_available | yes | 4520 | `SystemBench/ADRS/cloudcast/initial_program.py` |
| `systems:skyplane` | fetch_open | cached | yes | 38537 | `deployments/memex-sr/.cache/cloudcast_sources/systems_skyplane/source.html` |
| `systems:cloudmpcast` | skip_metadata_only | landing_only | no | 0 | `` |
| `systems:spanstore` | queue_mit_manual | needs_mit_operator | no | 0 | `` |
| `systems:b4` | queue_mit_manual | needs_mit_operator | no | 0 | `` |
| `systems:swan` | queue_mit_manual | needs_mit_operator | no | 0 | `` |
| `systems:ron` | queue_mit_manual | needs_mit_operator | no | 0 | `` |
| `systems:end-system-multicast` | skip_metadata_only | landing_only | no | 0 | `` |
| `systems:splitstream` | queue_mit_manual | needs_mit_operator | no | 0 | `` |
| `systems:bullet` | fetch_open | fetched | yes | 330506 | `deployments/memex-sr/.cache/cloudcast_sources/systems_bullet/source.pdf` |
| `systems:bittorrent` | fetch_open | cached | yes | 81110 | `deployments/memex-sr/.cache/cloudcast_sources/systems_bittorrent/source.pdf` |
| `systems:kraken` | skip_metadata_only | landing_only | no | 0 | `` |
| `systems:netstitcher` | skip_metadata_only | landing_only | no | 0 | `` |
| `algorithms:directed-steiner-charikar` | queue_mit_manual | needs_mit_operator | no | 0 | `` |
| `algorithms:steiner-tree-survey` | queue_mit_manual | needs_mit_operator | no | 0 | `` |
| `algorithms:network-flows-book` | queue_mit_manual | needs_mit_operator | no | 0 | `` |
| `algorithms:multicommodity-flow-survey` | skip_metadata_only | landing_only | no | 0 | `` |
| `algorithms:column-generation` | fetch_open | cached | yes | 64372 | `deployments/memex-sr/.cache/cloudcast_sources/algorithms_column-generation/source.html` |
| `algorithms:benders-decomposition` | fetch_open | fetched | yes | 57721 | `deployments/memex-sr/.cache/cloudcast_sources/algorithms_benders-decomposition/source.html` |
| `implementation:pulp` | fetch_open | cached | yes | 12867 | `deployments/memex-sr/.cache/cloudcast_sources/implementation_pulp/source.html` |
| `implementation:networkx-shortest-paths` | fetch_open | cached | yes | 81717 | `deployments/memex-sr/.cache/cloudcast_sources/implementation_networkx-shortest-paths/source.html` |
| `implementation:or-tools-min-cost-flow` | fetch_open | cached | yes | 264618 | `deployments/memex-sr/.cache/cloudcast_sources/implementation_or-tools-min-cost-flow/source.html` |
| `implementation:scipbook` | fetch_open | cached | yes | 9876 | `deployments/memex-sr/.cache/cloudcast_sources/implementation_scipbook/source.html` |
| `cloud-economics:aws-data-transfer` | fetch_open | cached | yes | 226514 | `deployments/memex-sr/.cache/cloudcast_sources/cloud-economics_aws-data-transfer/source.html` |
| `cloud-economics:gcp-network-pricing` | fetch_open | cached | yes | 3695948 | `deployments/memex-sr/.cache/cloudcast_sources/cloud-economics_gcp-network-pricing/source.html` |
| `cloud-economics:azure-bandwidth` | fetch_open | cached | yes | 211100 | `deployments/memex-sr/.cache/cloudcast_sources/cloud-economics_azure-bandwidth/source.html` |

`queue_mit_manual` records are not downloaded by this script. Retrieve them through approved MIT/operator workflows, put the files in the cache, and rerun acquisition with explicit provenance.
