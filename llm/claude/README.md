# Claude Skill

Last Oasis Modkit knowledge packaged as a [Claude Skill](https://docs.claude.com/) — auto-triggers in Claude Code or Claude Desktop on any Last Oasis modding mention.

## Files

| File | Description |
| --- | --- |
| [`claude-skill.zip`](claude-skill.zip) | The packaged skill bundle. Unzip and install. |

The zip contains `SKILL.md` (the skill instructions, with frontmatter triggers and the four workflows) and `last-oasis-modkit.skill` (the packaged skill file).

## Install

**Claude Code** (CLI / IDE extension):
1. Unzip `claude-skill.zip`.
2. Drop the contents into `~/.claude/skills/last-oasis-modkit/` (or your project's `.claude/skills/`).
3. The skill appears in your skill list and auto-triggers on Last Oasis modding mentions.

**Claude Desktop**:
1. Skills → Add skill → point at the unzipped folder.

## What it covers

The skill's `SKILL.md` frontmatter triggers on mentions of: Modkit, the Mist project, Steam Workshop publishing, MyRealm, Blueprint API questions, and a few related terms (the snapshot also lists `SDKTest` as a trigger — that branch is no longer required for modded play, but the skill still recognises the term). Once active, it branches into four workflows:

1. **Onboarding** — new modder, first install
2. **Reference Q&A** — Blueprint API, schema, settings
3. **Project coaching** — multi-step mod authoring help
4. **Troubleshooting** — packaging errors, server boot failures, etc.

The skill cites the data in [`../../data/`](../../data/) and the docs in [`../../docs/`](../../docs/).

## Generic alternative

If you're not on Claude, use the portable system prompt in [`../others/`](../others/) instead — same knowledge, different format.
