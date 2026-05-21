# Source Acquisition For Papers And Textbooks

Memex-SR should acquire reference material through a staged pipeline:

1. Enumerate paper/textbook targets.
2. Plan acquisition for each candidate URL or local asset.
3. Fetch only open material automatically.
4. Queue MIT-authenticated or licensed material for operator-assisted
   retrieval.
5. Parse only local cached assets.
6. Publish graph facts from manifests, never from live network calls.

This is deliberate. An MIT account expands lawful access, but it does
not make bulk scripted downloading of licensed journals or ebooks safe.
MIT Libraries documents the normal access paths through MIT IP, VPN, or
Touchstone/libproxy, and separately says licensed resources are for
noncommercial research, education, and scholarship with reasonable
portion download/print use. It also points users to Search Our
Collections, LibKey Nomad, and ILLiad for getting materials.

References:

- [Authenticate to online resources](https://libraries.mit.edu/research-support/connect/)
- [Using licensed resources](https://libraries.mit.edu/scholarly/publishing/using-licensed-resources/)
- [Get materials via the MIT Libraries](https://libraries.mit.edu/research-support/get-materials-from-the-libraries/)
- [Interlibrary Borrowing via ILLiad](https://libraries.mit.edu/docs/ilb/)

## Acquisition Lanes

| Lane | Automation | Examples | Output |
|---|---:|---|---|
| Open direct | Yes, host-policy governed | USENIX PDFs, PVLDB PDFs, arXiv, OpenReview, RFCs, OCW/course notes | cached file + acquired asset manifest |
| Open repository / author copy | Yes after URL verification | author PDFs, project reports, lab tech reports | cached file + provenance |
| MIT library manual | No scripted download | ACM/IEEE/Springer/Wiley/ebook access through browser, LibKey, Search Our Collections, ILLiad | operator task, then local file manifest |
| Operator supplied | No network | collaborator PDF, licensed local chapter, textbook excerpt | local file manifest |
| Metadata only | No full text | DOI landing page, publisher landing page, abstract page | skip state + coverage |
| Denied | No | disallowed host/access basis | blocked state + reason |

## What The Planner Does

`scripts/plan_acquisition.py` is the first backend seam. It reads:

- `manifests/paper_cut.json`;
- `acquisition_policy.yaml`;
- `download_host_policy.yaml`;
- `textbook_sources.yaml`.

It writes an acquisition plan, not downloaded files. Each record says
which action is allowed:

- `fetch_open`: safe for a downloader worker, subject to host policy;
- `queue_mit_manual`: create an operator task with a DOI/proxy/browser
  target, but do not script authentication;
- `queue_operator_asset`: wait for a local file;
- `skip_metadata_only`: keep as metadata/coverage only;
- `skip_denied`: blocked by policy.

Example:

```bash
uv --project external/okg run \
  python "$PWD/deployments/memex-sr/scripts/plan_acquisition.py" \
    --out /tmp/memex-sr-acquisition-plan.json \
    --include-textbooks
```

The downloader should consume only `fetch_open` records. The parser
should consume only `acquired_assets.jsonl` records whose local file,
hash, access basis, and provenance are present.

## Cloudcast Reviewed Source Slice

The Cloudcast actionable-context work has a separate reviewed seed
manifest:

- `fixtures/cloudcast_sources.yaml`
- `scripts/plan_cloudcast_acquisition.py`

The manifest is intentionally broader than the current graph. It covers
benchmark-local artifacts, direct systems comparators, algorithmic
foundations, implementation/data-structure guidance, and cloud-pricing
sources. Holdout artifacts such as `optimal.py` and
`task_prompt_direction_with_optimal.txt` are listed only so the planner
can prove they are excluded.

Dry-run the Cloudcast acquisition plan without network access:

```bash
uv --project external/okg run \
  python "$PWD/deployments/memex-sr/scripts/plan_cloudcast_acquisition.py" \
    --out "$PWD/deployments/memex-sr/reports/cloudcast-ab/cloudcast-acquisition-plan.json" \
    --markdown-output "$PWD/deployments/memex-sr/reports/cloudcast-ab/cloudcast-acquisition-plan.md"
```

The output records target files, cache paths, access basis, allowed
action, and host rate policy. It is the handoff artifact for deciding
which open sources can be fetched automatically and which MIT/manual
items need operator retrieval.

To diagnose whether an OKG-assisted run actually used graph evidence,
run:

```bash
uv --project external/okg run \
  python "$PWD/deployments/memex-sr/scripts/diagnose_cloudcast_okg_usage.py" \
    --run-dir "$PWD/results/codex_okg_mcp_cloudcast/20260520T123410Z" \
    --dsn postgres://postgres:okg@localhost:5433/engram_memex_sr_profile_smoke \
    --output "$PWD/deployments/memex-sr/reports/cloudcast-ab/okg-usage-diagnostic.md" \
    --json-output "$PWD/deployments/memex-sr/reports/cloudcast-ab/okg-usage-diagnostic.json"
```

That diagnostic classifies a run as `okg_attached_but_underused` when
the MCP server was available but the agent did not cite Cloudcast
evidence before coding or evaluation.

## Reuse From `af_pubs`

The `af_pubs` deployment has the right implementation patterns for the
next steps:

- cache-first PDF acquisition with stable cache names;
- bounded concurrent downloads with retry/backoff and explicit outcome
  labels;
- parse separation: download cache misses first, then parse local PDFs;
- parser fingerprints in source progress so unchanged reruns skip work;
- PDF text extraction with page counts, warnings for no text layer, and
  optional line/bbox indexes;
- structure-aware section/table/figure extraction where domain
  heuristics are appropriate.

Memex-SR should reuse those mechanics, but not the AF-specific cover
page, supersedure, publication-family, or military publication section
heuristics. Papers and textbooks need their own document structure
parser and chunker.

## MIT-Authenticated Material

For subscription-only articles or ebooks:

- the planner may create a manual queue item with DOI, title, publisher
  landing page, and `libproxy.mit.edu/login?url=...` browser URL;
- a human MIT user retrieves the item through approved library/browser
  paths;
- the file is placed under `deployments/memex-sr/operator_assets/`
  or a configured private cache;
- the operator records an acquired manifest entry with access basis
  `licensed_local` or `mit_authenticated`.

No source adapter or publish cycle should log into Touchstone, reuse
browser cookies, or systematically download from publisher platforms.

## Textbooks

Textbooks need stricter handling than papers:

- open textbooks and official course notes can enter the open lane;
- licensed ebooks or chapters are manual/operator-supplied only;
- whole-book bulk acquisition is disabled by default;
- chunking should preserve chapter/section provenance, page ranges when
  available, and local access basis.

The target list lives in `textbook_sources.yaml`. Entries are disabled
unless they are open and low-risk or explicitly enabled by an operator.

## Backend Contract

The backend pipeline should have these durable steps:

1. `plan_acquisition`: deterministic, no network, reads metadata
   manifests and writes a plan.
2. `fetch_open_assets`: networked, cache-first, host-policy governed,
   consumes only `fetch_open`.
3. `record_operator_assets`: deterministic, hashes local files and
   writes acquired manifest rows.
4. `parse_assets`: deterministic over `(content_hash, parser_version,
   chunker_version)`.
5. `publish_full_text`: reads parse manifests and emits OKG facts.

Unchanged reruns should append zero facts. Parser/chunker version
changes should invalidate only affected assets.
