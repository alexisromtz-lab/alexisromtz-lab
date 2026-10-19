<!-- HUELLA-PERFIL-GITHUB-A2-20261019 -->

# Alexis Román — AI Infrastructure & CI Forensics

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Bash](https://img.shields.io/badge/Bash-4EAA25?style=flat-square&logo=gnubash&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)
![Zenodo](https://img.shields.io/badge/Zenodo_—_3_DOIs-1682D4?style=flat-square&logo=zenodo&logoColor=white)

I work on **failure diagnosis at the systems level**: CI pipelines, LLM inference serving, and
evaluation harnesses. My working rule is that *a number that cannot differ is not evidence* — every
claim below carries the object that produced it, and every gate I ship fails closed when it has
nothing to measure.

**Full record:** [Open Source Diagnostics — a measured record](https://github.com/alexisromtz-lab/platino-labs/blob/main/HISTORIAL_DIAGNOSTICOS_OS_20261019.md)

---

## Featured work

### 1. Scalable-context evaluation — same accuracy, 11.35× cheaper

A controlled 50-problem comparison on one corpus, two arms:

| arm | setup | result | cost |
|---|---|---|---|
| **A** | frontier reasoning model, no scaffolding | 50/50 correct | `0.265545000` |
| **B** | lightweight model + fail-closed structural gate (validators + bounded retries) | 50/50 correct | `0.023394983` |

Accuracy ties; cost does not. Measured ratio **11.3505×** — arm B costs **8.81 %** of arm A. The gate
itself was a non-factor in repair (0.2000 retries per problem): the structure lived in the answer
format, not in error recovery.

Verified artifacts (all three DOIs resolve, checked 2026-10-19):

- **Software `platino-core` v0.1.1** — [10.5281/zenodo.23459450](https://doi.org/10.5281/zenodo.23459450)
- **Measured corpus v0.1.1** — [10.5281/zenodo.23288831](https://doi.org/10.5281/zenodo.23288831)
- **Paper M5, pre-registered prediction (fulfilled at 768 s)** — [10.5281/zenodo.23363121](https://doi.org/10.5281/zenodo.23363121)

### 2. CI forensics in `tenstorrent/tt-metal` — one missing decorator, 12 blocked PRs

Two shards, `[sim_wh_n150]` and `[sim_bh_p150]`, were red across many unrelated open PRs. Almost every
author was reading the failure as their own.

Root cause: `tests/ttnn/unit_tests/operations/transformers/test_prefetcher_worker_pipes.py` calls
`device.load_sub_device_manager(...)` without the `@skip_for_slow_dispatch` guard that its sibling
`test_prefetcher.py` carries, producing
`TT_FATAL @ sub_device_manager_tracker.cpp:118: Using sub device managers is unsupported with slow dispatch`.

Evidence used before claiming independence:

- the culprit path is **absent from the diff** of every affected PR (12/12 checked);
- the failure signature is in the job log (`sub_device_manager_tracker.cpp:118` → 6–9 hits per red job),
  with `pipes>0` as the positive control for the grep;
- the same `TT_FATAL` reproduces on an unrelated branch and an unrelated PR run.

Delivered as **13 diagnostic comments across 12 open PRs** — no competing PRs opened. Where a job was
red for a *different* reason (8 of the candidates), it was excluded with the measured cause instead of
being handed a reusable diagnosis.

### 3. `vllm-project/vllm-omni` — 4 open pull requests

- **Timeout error mapping + `open_session` timeout.** The client waits 60 s, the server default was
  10 s, and `code="timeout"` did not exist in the wire protocol's error buckets — so a *server* timeout
  was reported to clients as `invalid_request_error` (a client fault). The message is a composite f-string
  that greps to 0 in source; the defect traces to a single emit site.
- **Client handshake budget** honoured when opening a duplex session (the only override in the tree was
  in `warmup.py`; no environment variable reached the serving path).
- **Docs:** `run_server.sh` override defaults aligned with the scripts; broken relative links to the
  serving API guides.

Plus a full root-cause write-up on issue **#9072** (CI failure, "duplex open timed out"), with the
variable that was silently double-defined and the one-line fix for the error taxonomy.

---

## What I actually do

- **Differential diagnosis under noise** — separate "this PR broke it" from "the harness broke it", and
  prove which one before speaking.
- **Fail-closed instrumentation** — a gate with an empty universe returns red (`RC 31`), never a green.
  A check that searches for one shape does not certify the absence of the others.
- **Cost accounting for inference** — same-accuracy comparisons priced per problem on real runs.

## Toolbox

Python · Bash · GitHub Actions (workflow authority topology, SHA-pinned actions, OIDC sinks) · pytest &
property-based testing · AST / YAML validation · LLM serving (vLLM) · reproducibility bundles (CFF,
Zenodo, ORCID).

## Elsewhere

- **ORCID** — [0009-0001-9116-075X](https://orcid.org/0009-0001-9116-075X)
- **Software & corpus** — [github.com/alexisromtz-lab](https://github.com/alexisromtz-lab)
