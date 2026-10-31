# Evals

Small, reproducible checks of what the skill changes. They measure injected instructions in single turns, not
automatic skill discovery or long conversations.

- [cases/hard-pressure.json](cases/hard-pressure.json): 8 scenarios with criteria fixed before generation.
- [run_codex.py](run_codex.py): generation runner for the Codex CLI. Uses your existing ChatGPT login; no API key.
- [results/](results/): reports with tables, examples and limits. Latest:
  [2026-10-30, GPT-6.1 Terra high](results/2026-10-30-gpt-6.1-terra-high.md).

## Run it

```sh
python3 evals/run_codex.py \
  --dataset evals/cases/hard-pressure.json \
  --skill skills/assertive-clarity/SKILL.md \
  --arms baseline,skill --attempts 5 --concurrency 1 \
  --model gpt-6.1-terra --effort high \
  --out eval-runs/hard-pressure-$(date +%Y%m%d)
```

Each call is a request to OpenAI and counts against your Codex usage. Responses land in `--out`, one folder per
case, arm and attempt. The runner refuses to start while `$CODEX_HOME/AGENTS.md` exists, because Codex applies that
file to every arm.

Judging is done separately: one blind call per scenario with the responses labeled A/B in random order, the skill
name removed, and the scenario's criteria. The judge script is not included yet; the reports state the method.

Results from other models are welcome as issues, with the model, settings and raw responses.
