# Sources

Each `*-docs.md` / `*-issues.md` / `*-recipe.md` page is the agent's summary of
one ingested upstream source: key takeaways, the claims it extracted, and links
into `../concepts/` and `../entities/`.

The **raw** corpus those summaries were distilled from (908 documents — cloned
repositories, rendered documentation, and a GitHub issue dump) is not
redistributed here. Instead the upstream repositories are pinned as git
submodules under `upstream/`, at the commits that were current when the wiki
was built:

| Summary page | Upstream |
|---|---|
| `verl-docs.md`, `verl-issues.md`, `verl-recipe.md` | [volcengine/verl](https://github.com/volcengine/verl) |
| `trl-docs.md` | [huggingface/trl](https://github.com/huggingface/trl) |
| `openrlhf-docs.md` | [OpenRLHF/OpenRLHF](https://github.com/OpenRLHF/OpenRLHF) |
| `nemo-rl-docs.md` | [NVIDIA-NeMo/RL](https://github.com/NVIDIA-NeMo/RL) |
| `slime-docs.md` | [THUDM/slime](https://github.com/THUDM/slime) |
| `miles-docs.md` | [radixark/miles](https://github.com/radixark/miles) |

To fetch them:

```bash
git submodule update --init --recursive framework/skills/wiki/sources/upstream
```

The submodules are optional: nothing in this repository imports from them. They
are here so that the provenance of every wiki claim can be checked against the
exact upstream state that was ingested.

The `Raw location:` field at the top of each summary page refers to the
original ingestion layout and is kept verbatim, pointing into the 908-document
raw corpus that is not redistributed.
