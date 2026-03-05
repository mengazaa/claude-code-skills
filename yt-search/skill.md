# YouTube Search Skill

Search YouTube directly from Claude Code via yt-dlp. Returns structured video results with title, channel, views, subscribers, duration, date, and direct URL. Includes auto-retry for timeout recovery and date filtering.

## Dependencies

- `yt-dlp` (installed via pip/brew)

## When to Use This Skill

Trigger when user:
- Wants to search YouTube for videos on a topic
- Mentions "yt-search", "search youtube", "find youtube videos"
- Needs YouTube URLs for NotebookLM pipeline

## Before Searching: Ask the User

If the user only provides a query (no flags), **ask 2 questions** before running the search:

1. **จำนวนวิดีโอ**: "อยากได้กี่วิดีโอครับ? (default: 20)"
2. **ช่วงเวลา**: "ช่วงเวลาไหนครับ? เช่น 'within feb 2026', 'last 3 months', หรือ 'ไม่จำกัด'"

If the user already provides flags (--count, --within, --months, etc.), skip asking and run directly.

## NotebookLM Source Limit Warning

If user mentions using results with NotebookLM, warn about source limits:

| Plan | Max Sources/Notebook | Max Notebooks |
|------|---------------------|---------------|
| Free/Standard | 50 | 100 |
| Plus | 100 | 200 |
| Pro | 300 | 500 |
| Ultra | 600 | 500 |

If `--count` exceeds user's plan limit, warn: "NotebookLM [Plan] รับได้สูงสุด [N] sources ต่อ notebook ครับ ต้องการลดจำนวนไหม?"

## Time Period Translation

Convert the user's answer to the right flag:
- "within feb 2026" or "เฉพาะ ก.พ. 2026" → `--within "feb 2026"`
- "last 3 months" or "3 เดือนล่าสุด" → `--months 3`
- "after jan 2026" or "หลัง ม.ค. 2026" → `--after "jan 2026"`
- "ไม่จำกัด" or "all time" → `--no-date-filter`
- (no answer / default) → `--months 6`

## Execute

Build and run the command with the user's answers:

```bash
python3 ~/.claude/skills/yt-search/scripts/search.py <query> --count <N> <time-flag>
```

## Available Flags

| Flag | Example | Description |
|------|---------|-------------|
| `--count N` | `--count 10` | Number of results |
| `--months N` | `--months 3` | Last N months |
| `--within "month year"` | `--within "feb 2026"` | Specific month only |
| `--after "date"` | `--after "jan 2026"` | After this date |
| `--before "date"` | `--before "mar 2026"` | Before this date |
| `--no-date-filter` | | All time |
| `--json` | | JSON output (includes description, tags, categories) |
| `--urls-only` | | Output URLs only (for piping to notebooklm) |
| `--cookies-from-browser` | `--cookies-from-browser safari` | Use browser cookies |
| `--no-cookies` | | Disable browser cookies |

## Output Format

Each result shows:
- Title
- Channel name + subscriber count
- View count + views/subs ratio
- Duration
- Upload date
- Direct YouTube URL

## Auto-Retry Behavior (Built-in)

The script handles timeout failures automatically — no manual intervention needed:

| Failure | Auto-behavior |
|---------|--------------|
| **Timeout with Chrome cookies** | Retries automatically without cookies |
| **Timeout without cookies** | Exits with error message |

**Bot detection error** ("Sign in to confirm you're not a bot") is different from timeout — it appears in output text, not as a timeout. If this happens: add `--cookies-from-browser safari` (or `chrome` / `firefox`) to the command manually.

## Zero Results Strategy

If search returns 0 results, suggest broadening the query:

- Too specific: `"OpenClaw usecases"` → broaden to `"OpenClaw"` or `"OpenClaw Samin Yasar"`
- Add channel/person name to narrow back down once you find results
- Try removing niche terms (e.g., "usecases", "tutorial", "how to") and search by topic only

## Integration with NotebookLM

Use `--urls-only` flag to get clean URLs for NotebookLM source add:

1. Search: `python3 ~/.claude/skills/yt-search/scripts/search.py "topic" --count 20`
2. Create notebook: `notebooklm create "Research: Topic"`
3. Add sources: Add each YouTube URL as a source (parallel batches of 7)
4. Analyze: Ask NotebookLM questions about the content

## Examples

```bash
# Basic search
python3 ~/.claude/skills/yt-search/scripts/search.py "claude code skills" --count 10

# Specific month
python3 ~/.claude/skills/yt-search/scripts/search.py "AI agents" --count 20 --within "feb 2026"

# URLs only (for piping to notebooklm)
python3 ~/.claude/skills/yt-search/scripts/search.py "OpenClaw" --count 50 --urls-only

# JSON output
python3 ~/.claude/skills/yt-search/scripts/search.py "AI automation" --count 20 --json

# No date filter
python3 ~/.claude/skills/yt-search/scripts/search.py "react tutorial" --no-date-filter --count 5
```

## Script Location

`~/.claude/skills/yt-search/scripts/search.py`

Present the output directly to the user. If the script reports an error, explain it and suggest fixes.
