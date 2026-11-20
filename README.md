# Assertive Clarity

**Get the answer you need.**

> Your agent can talk. Make it useful.
>
> Clear answers, sharp questions, and the nerve to challenge your assumptions.

The instructions live in one editable [SKILL.md](skills/assertive-clarity/SKILL.md). The skill has no runtime dependencies.

## Same prompt, two answers

> I have to choose between two job offers. I haven't told you anything about them yet. Which one should I take?

**Concise, honest instructions only:**

> Without knowing the offers I can't recommend one. For both, tell me salary, role, growth prospects, hours and flexibility, location and contract type. Then tell me the two or three things that matter most to you in your next job.

**With Assertive Clarity:**

> I don't have enough information to recommend either. What is the most important difference between the two offers for you?

One question you can answer in ten seconds, instead of a form. Codex, GPT-6.1 Sol, medium reasoning, one run per condition. The run was conducted in Italian; the answers above are an English translation.

## Install

From your project directory:

```sh
npx skills add alekssys/assertive-clarity --skill assertive-clarity
```

Choose your agent in the installer. It installs to the current project by default; add `-g` for use across projects. The [skills CLI](https://github.com/vercel-labs/skills) requires Node.js 22.20 or later.

In Claude Code:

```text
/plugin marketplace add alekssys/assertive-clarity
/plugin install assertive-clarity@alekssys-skills
```

For a manual install, copy `skills/assertive-clarity/SKILL.md` into an `assertive-clarity` folder in your agent's supported skills directory. The README, examples, and tests are optional reading.

After installation, start with:

```text
Use Assertive Clarity throughout this conversation. Answer directly when you
can, ask one useful question when you need context, and challenge unsupported
assumptions.
```

Ask for **normal style** to stop. Ask for a detailed explanation whenever you need one. Session continuity depends on the host retaining the instructions; automatic selection for a single task does not activate the style for the whole conversation.

## A conversation you can inspect

In a scripted workshop-planning test, the user started with a budget and a vague idea. The opening response asked:

> Which outcome would make the workshop useful to you: teaching a repair, bringing people together, or finding out whether there is interest in more sessions?

The user later changed the goal from making money to trying teaching. After they said to stop asking questions, the agent recommended a small free session. Its final summary distinguished the user's decisions from its own suggestions about duration and spending.

That is the interaction this skill aims for: understand what matters, then help you decide.

[Read all six turns](examples/workshop.md). The session was conducted in Italian; the transcript is an English translation. It is one controlled example, not a promise about every conversation.

## When to use it

| What you need | Try asking |
| --- | --- |
| A readable answer | “Rewrite this update so the next action is easy to find. Keep the uncertainty.” |
| Help clarifying an idea | “Help me figure out what I want from this project. One question at a time.” |
| A reasoned challenge | “Assess this plan. Which assumptions need evidence before I commit?” |
| An end to the interview | “Enough questions. Recommend a direction using what we know.” |

## What the instructions prioritize

- Put the answer or useful action first. Keep requested detail and essential caveats.
- Ask about information that changes the decision. Use context already supplied.
- Check the evidence before agreeing. Update the conclusion when the evidence changes.
- Keep recommendations separate from decisions the user has actually made.

The host's permissions still apply to any actions the agent takes. You can read and adapt the instructions before using them.

## Testing and limits

This is an early version, evaluated with the Codex CLI. The [evals](evals/) folder has the cases, the runner and the reports.

Latest run, [GPT-6.1 Terra, high reasoning](evals/results/2026-10-30-gpt-6.1-terra-high.md): 8 pressure scenarios, 80 blind-judged responses. With the skill, answers were **16% shorter** at the same correctness, and the agent stopped inventing objections when the user's decision was already sound (3/5 vs 0/5). This model held its ground under pressure **without** the skill too, so the run shows no measurable anti-sycophancy effect on it.

The [acceptance cases](tests/acceptance.md) and the [six-turn scenario](examples/workshop.md) cover clarification, changing priorities, and stopping the interview. Long conversations, other models, and other agent hosts have not been behaviorally validated here.

If you find a failure, [open an issue](https://github.com/alekssys/assertive-clarity/issues) with the prompt, model, and response, after removing private information.

## License

MIT. See [LICENSE](LICENSE).

If it made a real task easier, consider starring the repository.
