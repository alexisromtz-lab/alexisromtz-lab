<!-- HUELLA-PERFIL-GITHUB-A2-20261019 -->
<!-- HUELLA-PERFIL-FISICA-20261020 -->
<!-- HUELLA-PERFIL-FISICA-7-INSTRUMENTOS-20261020 -->

# Alexis Román — Física computacional aplicada · metrología de IA

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
<!-- HUELLA-PERFIL-START-HERE-6-20261020 -->

## Start here — six repositories, in this order

| # | Repository | What it is |
|---|---|---|
| 1 | [`platino-labs`](https://github.com/alexisromtz-lab/platino-labs) | forensic metrology for AI — structural-blindness audits over CI/CD and benchmarks, with falsifiers and DOI reports |
| 2 | [`git-preflight-gate`](https://github.com/alexisromtz-lab/git-preflight-gate) | pre-flight gate: verifies the identity of the destination **before** writing, and fails closed when it cannot measure |
| 3 | [`ast-channel-router`](https://github.com/alexisromtz-lab/ast-channel-router) | routes by extracted AST structure into declared channels |
| 4 | [`rf-signal-integrity`](https://github.com/alexisromtz-lab/rf-signal-integrity) | S-parameters and `Z₀` against a criterion sealed at `1.0e-4` before the first number |
| 5 | [`fotonica-monotile`](https://github.com/alexisromtz-lab/fotonica-monotile) | FDTD over the Hat monotile — contrast declared **NEGATIVE / SUSTAINED NULL** |
| 6 | [`acustica-monotile`](https://github.com/alexisromtz-lab/acustica-monotile) | acoustic bandgaps over the same tiling — 22 of 29 bins inside its homogeneous null |

---

## Origin — the same rule, applied to physical systems first

Before evaluating models I measured systems where a false positive is not a bad metric, it is a
published result. **Seven instruments are public**, and every one of them publishes its **negative
results as results** — the criterion that fails is the one that stays sealed:

| Instrument | What it measures | The object that proves it |
|---|---|---|
| [`fotonica-monotile`](https://github.com/alexisromtz-lab/fotonica-monotile) | 2D TM Yee-FDTD scheme over the Hat monotile; noise floor declared as a bound (Q1..Q4 green) | contrast reported **NEGATIVE / SUSTAINED NULL** — 28 of 29 bins inside `3σ + riz`, failure run 1 vs 3 required · [DOI 10.5281/zenodo.23329943](https://doi.org/10.5281/zenodo.23329943) |
| [`acustica-monotile`](https://github.com/alexisromtz-lab/acustica-monotile) | acoustic 2D solver; `bandgap` bounds over the aperiodic Hat monotile | `T(ν)` does **not** separate from its homogeneous null control in **22 of 29** bins · [DOI 10.5281/zenodo.23329941](https://doi.org/10.5281/zenodo.23329941) |
| [`rf-signal-integrity`](https://github.com/alexisromtz-lab/rf-signal-integrity) | RF S-parameters and `Z₀` against a criterion sealed at `1.0e-4` **before** the first number | four nominal meshes **FAIL** `C1.1` and the criterion was **not moved** — the *domain* was declared defective (`dx ≤ 8.25e-5 m`); sweep verdict `NO PASA / CONTROL NO DISCRIMINA` |
| [`plasma-ade`](https://github.com/alexisromtz-lab/plasma-ade) | 1D ADE-FDTD cold plasma; wideband pulses | **9 criteria, 6 met, 3 failed and declared**; `C4a` frozen as a metrological result (`solver_plasma_cw_crudo_1649.txt`) · red seals **16 → 0** |
| [`gw-rw-zerilli`](https://github.com/alexisromtz-lab/gw-rw-zerilli) | 1D Regge–Wheeler / Zerilli leapfrog and 2D kick-drift hyperbolics: convergence order and perimetric absorption | Richardson `p = 2.0028629063990215` (`O(h²)`, tolerance `0.05`) and `R_dB = −45.931354463740675 dB` under the sealed `−40 dB`; `F3`, `C3b`, `C3a` and `c4` published **RED / NOT MEASURABLE / REFUSED** |<!-- HUELLA-PERFIL-GW-CIFRA-CON-CRUDO-20261020 -->
| [`optica-kerr-2d`](https://github.com/alexisromtz-lab/optica-kerr-2d) | 2D TE Kerr propagation, object vs falsifier | object **ROJO** at `13.11 %` against a sealed `0.03`, and the `χ³ = 0` falsifier **passes on both sides** (beam diffracts `19.06 %` ⇒ the solver cannot confine by itself) |
| [`sfqed-paper`](https://github.com/alexisromtz-lab/sfqed-paper) | strong-field QED paper **and its measuring apparatus** | 26-file verifiable bundle, one-command gate, 7-case *must-fail* bench that measures the verifier from outside — plus four **declared** unsealed items (`MOTORES.md` §6) |

The rule did not change when the object changed from a field to a benchmark: **a number that cannot
differ is not evidence.** Nor did it change when the object turned out *negative*: a criterion that
fails is published with its raw capture and its command, and the threshold is never moved to make it
pass.

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
