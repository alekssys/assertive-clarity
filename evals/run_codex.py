#!/usr/bin/env python3
"""Small, keyless Codex CLI evaluation runner. Uses the CLI's existing login.

This tests injected instructions, not skill discovery or multi-turn persistence.
No credential is read, copied, or translated. All generated artifacts stay in out.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import time

COMMON = "Answer the user's request in their language. Do not use tools or access files. Return only the response to the user."
GENERIC = "Be concise, clear, honest, and actionable. Ask a clarifying question only when necessary. Do not agree with unsupported claims."
DISABLE = ["apps", "plugins", "remote_plugin", "hooks", "memories", "multi_agent", "shell_tool", "unified_exec", "browser_use", "computer_use", "image_generation", "goals", "workspace_dependencies"]


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def parse_events(raw, returncode):
    events, malformed = [], 0
    for line in raw.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    completed = [e for e in events if e.get("type") == "turn.completed"]
    failures = [e for e in events if e.get("type") in {"turn.failed", "error"}]
    replies = [e["item"].get("text", "") for e in events
               if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
    tool_items = [e.get("item", {}).get("type") for e in events
                  if e.get("type") == "item.completed"
                  and e.get("item", {}).get("type") not in {"agent_message", "reasoning"}]
    text = "\n\n".join(replies)
    # Fail closed on process/transport failures or unexpected tool use.
    ok = returncode == 0 and bool(completed) and bool(text.strip()) and not failures and not malformed and not tool_items
    return {"status": "completed" if ok else "infrastructure_or_protocol_failure",
            "response": text, "usage": completed[-1].get("usage", {}) if completed else {},
            "tool_items": tool_items, "malformed_lines": malformed,
            "errors": failures, "words": len(text.split())}


def disabled_skills(workspace):
    roots = [Path.home()/".codex/skills", Path.home()/".agents/skills", Path("/etc/codex/skills")]
    for ancestor in [workspace, *workspace.parents]:
        roots.extend([ancestor/".agents/skills", ancestor/".codex/skills"])
    paths = set()
    for root in roots:
        if root.is_dir():
            for entry in root.rglob("SKILL.md"):
                # Older CLI versions used file paths; current docs use folders.
                paths.update([str(entry.absolute()), str(entry.parent.absolute()),
                              str(entry.resolve()), str(entry.parent.resolve())])
    return sorted(paths)


def global_agents_files():
    """Global Codex instructions are loaded even with --ignore-user-config.

    If they mention the skill (or any style rule), the baseline arm is no longer
    an agent without the skill. Return the files so main() can refuse to run.
    """
    home = Path(os.environ.get("CODEX_HOME", Path.home()/".codex"))
    return [p for p in (home/"AGENTS.md", home/"AGENTS.override.md") if p.is_file()]


def command(binary, workspace, model, effort, instructions, skill_paths):
    cmd = [binary, "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
           "--sandbox", "read-only", "--color", "never", "--json", "--cd", str(workspace),
           "--model", model, "-c", "approval_policy=\"never\"",
           "-c", "project_doc_max_bytes=0", "-c", "web_search=\"disabled\"",
           "-c", "model_reasoning_effort=" + json.dumps(effort),
           "-c", "developer_instructions=" + json.dumps(instructions)]
    entries = ",".join("{path=" + json.dumps(p) + ",enabled=false}" for p in skill_paths)
    cmd += ["-c", "skills.config=[" + entries + "]"]
    for feature in DISABLE:
        cmd += ["--disable", feature]
    return cmd + ["-"]


def run_trial(spec, args, binary, skills):
    case, arm, attempt, instructions = spec
    run = args.out / (case["id"] + "__" + arm + "__" + str(attempt))
    run.mkdir()
    workspace = run/"workspace"
    workspace.mkdir()
    (workspace/".git").mkdir()  # discovery boundary; no repository contents
    cmd = command(binary, workspace, args.model, args.effort, instructions, skills)
    if args.output_schema:
        cmd = cmd[:-1] + ["--output-schema", str(args.output_schema.resolve()), "-"]
    (run/"prompt.txt").write_text(case["prompt"])
    (run/"instructions.txt").write_text(instructions)
    (run/"command.json").write_text(json.dumps(cmd, indent=2))
    start = time.monotonic()
    env = dict(os.environ)
    # Force the already authenticated ChatGPT path, never an ambient API key.
    for key in ["OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"]:
        env.pop(key, None)
    env["TMPDIR"] = str(args.out/"tmp")
    try:
        result = subprocess.run(cmd, input=case["prompt"], capture_output=True, text=True,
                                timeout=args.timeout, env=env)
        raw, err, rc = result.stdout, result.stderr, result.returncode
        parsed = parse_events(raw, rc)
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout or b""
        err = exc.stderr or b""
        raw = raw.decode(errors="replace") if isinstance(raw, bytes) else raw
        err = err.decode(errors="replace") if isinstance(err, bytes) else err
        rc = None
        parsed = {"status": "timeout", "response": "", "usage": {}, "words": 0}
    (run/"events.jsonl").write_text(raw)
    (run/"stderr.txt").write_text(err)
    (run/"response.md").write_text(parsed.pop("response"))
    parsed.update(case_id=case["id"], arm=arm, attempt=attempt, returncode=rc,
                  seconds=round(time.monotonic()-start, 3), instructions_sha256=digest(instructions))
    (run/"result.json").write_text(json.dumps(parsed, indent=2))
    print(json.dumps({k: parsed[k] for k in ["case_id", "arm", "status", "seconds", "words"]}), flush=True)
    return parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--previous-skill", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--codex", default="codex", help="Codex CLI executable or absolute path")
    parser.add_argument("--output-schema", type=Path)
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--arms", default="baseline,generic,skill")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--seed", type=int, default=20261015)
    parser.add_argument("--allow-global-agents", action="store_true",
                        help="Run even if $CODEX_HOME/AGENTS.md exists (contaminates the baseline)")
    args = parser.parse_args()
    found = global_agents_files()
    if found and not args.allow_global_agents:
        parser.error("Global Codex instructions found: " + ", ".join(map(str, found)) +
                     ". They are applied to every arm. Move them aside for the run, or pass --allow-global-agents.")
    args.out = args.out.resolve()
    if args.attempts < 1 or not 1 <= args.concurrency <= 4 or args.timeout < 1:
        parser.error("Positive attempts/timeout and concurrency 1..4 required")
    arms = args.arms.split(",")
    if len(set(arms)) != len(arms) or set(arms)-{"baseline", "generic", "skill", "previous"}:
        parser.error("Arms must be unique baseline,generic,skill,previous values")
    if "previous" in arms and not args.previous_skill:
        parser.error("previous requires --previous-skill")
    data = json.loads(args.dataset.read_text())
    cases = data["evals"][:args.limit] if args.limit else data["evals"]
    ids = [c["id"] for c in cases]
    if not ids or len(set(ids)) != len(ids) or any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", i) for i in ids):
        parser.error("Case IDs must be nonempty, unique, and safe path components")
    binary = shutil.which(args.codex)
    if not binary:
        parser.error("codex CLI is required")
    login = subprocess.run([binary, "login", "status"], capture_output=True, text=True)
    if login.returncode or "ChatGPT" not in login.stdout + login.stderr:
        parser.error("Existing ChatGPT login required; run codex login separately")
    version = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    skill = args.skill.read_text()
    instructions = {"baseline": COMMON, "generic": COMMON + "\n\n" + GENERIC,
                    "skill": COMMON + "\n\nApply the following skill instructions for this request:\n\n" + skill}
    if args.previous_skill:
        instructions["previous"] = COMMON + "\n\nApply the following skill instructions for this request:\n\n" + args.previous_skill.read_text()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out/"tmp").mkdir()
    skills = disabled_skills(args.out)
    specs = [(c, a, i, instructions[a]) for c in cases for a in arms for i in range(1, args.attempts+1)]
    random.Random(args.seed).shuffle(specs)
    manifest = {"runner": "codex-cli-chatgpt", "codex_version": version,
                "model": args.model, "reasoning_effort": args.effort, "auth": "existing ChatGPT login",
                "skill_sha256": digest(skill), "dataset_sha256": digest(args.dataset.read_text()),
                "seed": args.seed, "attempts": args.attempts, "concurrency": args.concurrency,
                "global_agents_files": [str(p) for p in found],
                "arms": arms, "cases": ids, "disabled_skill_paths": skills,
                "scope": "single-turn injected-instruction efficacy; not native skill discovery or persistence",
                "limitations": ["Host/system instructions still apply", "Catalog disablement configured, not independently observed in raw model input", "Single model, small pilot; no statistical or clinical claims"]}
    manifest["runner_sha256"] = digest(Path(__file__).read_text())
    manifest["previous_skill_sha256"] = digest(args.previous_skill.read_text()) if args.previous_skill else None
    (args.out/"manifest.json").write_text(json.dumps(manifest, indent=2))
    (args.out/"dataset.json").write_text(json.dumps(data, indent=2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda spec: run_trial(spec,args,binary,skills), specs))
    (args.out/"results.json").write_text(json.dumps(results, indent=2))
    failed = [r for r in results if r["status"] != "completed"]
    print(json.dumps({"completed": len(results)-len(failed), "failed": len(failed), "out": str(args.out)}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
