# Assertive Clarity

A self-contained, agent-agnostic skill for readable answers, clearer decisions, and honest disagreement. It reduces conversational clutter while retaining the information needed to act.

The skill does not add a coding workflow, project-management system, external service, or dependency. The only file an agent needs is [SKILL.md](SKILL.md).

## Use it

Place `SKILL.md` in a folder named `assertive-clarity` inside the skills directory supported by your agent. Invoke `assertive-clarity` by name to use the communication style for the conversation; ask for normal style to stop. Activation and persistence depend on the host retaining the instructions. Automatic discovery may select it for a matching task without enabling it for the whole conversation.

Examples:

- “Use Assertive Clarity throughout this conversation. Keep answers readable and challenge unsupported assumptions.”
- “Choose between these two options. Tell me what would change your recommendation.”
- “Challenge my reasoning before I commit. One question at a time.”
- “Rewrite this update so my team can act on it quickly.”

## Design

The skill combines three behaviors:

- **Readable communication:** answers first, manageable steps, visible progress, realistic effort estimates, useful error reports, and one next action when work remains for the user. Complete explanations and lists stay complete.
- **Decision clarification:** questions that resolve meaningful uncertainty, one at a time, with a bounded challenge session when requested.
- **Anti-sycophancy:** assess claims independently of the user's preferred answer, resist pressure without becoming argumentative, and revise conclusions when evidence changes.

It uses the context already present and proceeds when a safe assumption is enough. Neither agreement nor disagreement is a goal in itself.

The skill guides communication and decision support. It does not grant the agent permission to access tools, change files, or act on the user's behalf.

## Validation

The [acceptance cases](tests/acceptance.md) cover communication, multi-turn behavior, and resistance to pressure. Structural validation and small qualitative checks do not establish reliable parity, token savings, or effectiveness across models. This is a candidate for broader evaluation; it cannot guarantee that a model will avoid sycophancy.

A local revision comparison completed 42 responses across 14 prompts using GPT-6.1 Sol with medium reasoning, comparing previous instructions, generic guidance, and this revision. Author review found improved clarification on one regression case, but a compound question remained in an additional case. This small, single-turn comparison does not establish superiority over generic guidance or verify native skill discovery and conversation persistence.

## License

MIT. See [LICENSE](LICENSE).
