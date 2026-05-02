# Generic system prompt

Last Oasis Modkit knowledge as a single Markdown file you can paste into any LLM that accepts a system prompt. Same domain content as the [Claude Skill](../claude/), in a portable form.

## Files

| File | Description |
| --- | --- |
| [`last-oasis-modkit-system-prompt.zip`](last-oasis-modkit-system-prompt.zip) | Single Markdown file inside. Unzip and use. |

## Install

Unzip and use the contained `.md` as the **system prompt** of your assistant of choice:

- **ChatGPT custom GPT** → *Create a GPT* → *Configure* → paste into **Instructions**.
- **Claude Project** → project settings → paste into **Custom Instructions**.
- **OpenAI Playground** → set as the `system` message.
- **Any OpenAI-compatible API** → pass as the first message with `role: "system"`.

The file's header explains each integration path in detail.

## When to use this vs the Claude Skill

| Use case | Use |
| --- | --- |
| You're on Claude Code or Claude Desktop | [`../claude/`](../claude/) — auto-triggers, no copy-paste |
| You're on ChatGPT, the OpenAI API, a non-Claude tool, or want a portable file | This (the generic system prompt) |
