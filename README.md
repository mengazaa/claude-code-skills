# Claude Code Skills: YouTube Search + NotebookLM CLI

Two self-contained Claude Code skills for YouTube research and NotebookLM automation.

## Skills

### yt-search
Search YouTube via yt-dlp with structured output, auto-retry, and date filtering.

**Features:**
- Structured results with title, channel, views, subscribers, duration
- Date filtering (--within, --after, --before, --months)
- Auto-retry on timeout (cookies → no-cookies fallback)
- JSON and URLs-only output modes
- NotebookLM integration (--urls-only for source add)

### notebooklm-cli
Control Google NotebookLM from Claude Code — create notebooks, add sources, generate deliverables (audio, video, quiz, flashcards, infographics, slide decks), and run analysis.

**Features:**
- Full notebook lifecycle (create, list, delete, rename)
- Source management (YouTube URLs, web URLs, PDFs, docs)
- Content generation with Creative Director Mode
- Parallel source adding (batches of 7)
- Pre-flight auth check

## Installation

1. Copy the skill folder(s) to `~/.claude/skills/`
2. Install dependencies:

```bash
# For yt-search
pip install yt-dlp

# For notebooklm-cli
uv tool install "notebooklm-py[browser]"
notebooklm login  # one-time Google auth
```

3. (Optional) Create slash commands in `~/.claude/commands/`:

**yt-search.md:**
```markdown
---
description: "Search YouTube and return structured video results"
argument-hint: "<query>"
allowed-tools:
  - Bash
---

Read the full skill documentation first:
~/.claude/skills/yt-search/skill.md
Then follow the skill instructions.
```

**notebooklm.md:**
```markdown
---
description: "Control NotebookLM - create notebooks, add sources, generate deliverables"
argument-hint: "<command> [args]"
allowed-tools:
  - Bash
---

Read the full skill documentation first:
~/.claude/skills/notebooklm-cli/skill.md
Then follow the skill instructions.
```

## Usage

### Via slash commands
```
/yt-search OpenClaw
/notebooklm create "My Research"
```

### Via natural language
```
Search YouTube for AI agents and create a NotebookLM notebook with the results
```

### Full pipeline
```
Search YouTube for "claude code skills", take top 20 results,
create a NotebookLM notebook, add all videos as sources,
then ask NotebookLM for the top trends and generate an infographic
```

## Dependencies

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube search/download
- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) — NotebookLM CLI
- [Claude Code](https://claude.ai/claude-code) — AI coding assistant

## License

MIT
