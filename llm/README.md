# LLM bundles

Drop-in prompts that pre-load an AI assistant with Last Oasis Modkit knowledge — UE 4.25.4, the `Mist` project, the `SDKTest` Steam branch, MyRealm setup, EAC quirks, the Blueprint API surface, and the contents of [`../data/`](../data/).

Both bundles are **snapshots from April 2026**. The Modkit moves quickly; both prompts tell the LLM to verify volatile claims against the [official Discord](https://discord.gg/lastoasis).

## Pick one

| Folder | Format | Best for |
| --- | --- | --- |
| [`claude/`](claude/) | Claude Skill bundle (`SKILL.md` + `.skill`) | Claude Code or Claude Desktop — auto-triggers on Last Oasis modding mentions, branches into onboarding / reference Q&A / project coaching / troubleshooting workflows. |
| [`others/`](others/) | Single Markdown file (system prompt) | Any other LLM that accepts a system prompt: ChatGPT custom GPT, Claude Project custom instructions, OpenAI Playground, etc. |

Both cover the same domain knowledge — pick by integration target, not by content.

Full repo overview: [`../README.md`](../README.md).
