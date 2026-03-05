# NotebookLM CLI Skill

Control Google NotebookLM from Claude Code via the `notebooklm` CLI (notebooklm-py by Tang Ling). Create notebooks, add sources (YouTube, URLs, files), generate deliverables (audio, video, quiz, flashcards, infographics, slide decks), and run analysis — all from the terminal.

Based on: https://github.com/teng-lin/notebooklm-py

## Dependencies

- `notebooklm-py` (installed via uv: `uv tool install "notebooklm-py[browser]"`)
- One-time login: `notebooklm login`

## When to Use This Skill

Trigger when user:
- Wants to create a NotebookLM notebook
- Wants to add YouTube videos or URLs as sources
- Wants to generate deliverables (audio, video, quiz, flashcards, infographic, slide deck, mind map, report)
- Wants to analyze content from multiple sources
- Uses phrases like "use notebooklm", "create notebook", "generate infographic from videos"

## Pre-flight: Auth Check

**ALWAYS run this first** before any NotebookLM operation:
```bash
notebooklm list
```
`notebooklm list` actually calls the Google API — if auth is expired it fails immediately.
(`notebooklm status` only shows local context, does NOT verify auth with Google.)

If `notebooklm list` fails → tell user to run `notebooklm login` in a separate terminal BEFORE starting any work.

## Authentication

Run once to authenticate with Google:

```bash
notebooklm login
```

This opens a browser for Google login. Credentials are stored securely in system keychain.

## NotebookLM Plan Limits

| Plan | Max Sources/Notebook | Max Notebooks | Max Words/Source |
|------|---------------------|---------------|------------------|
| Free/Standard | 50 | 100 | 500,000 |
| Plus | 100 | 200 | 500,000 |
| Pro | 300 | 500 | 500,000 |
| Ultra | 600 | 500 | 500,000 |

Warn user when approaching source limits.

## CLI Commands Reference

### Notebook Management

```bash
notebooklm create "Notebook Name"        # Create new notebook (returns notebook_id)
notebooklm list                           # List all notebooks
notebooklm use <notebook_id>              # Set active notebook
notebooklm rename <notebook_id> "Name"    # Rename notebook
notebooklm delete <notebook_id>           # Delete notebook
```

### Source Management

```bash
notebooklm source add "https://youtube.com/watch?v=..."   # Add YouTube video
notebooklm source add "https://example.com/article"       # Add web URL
notebooklm source add "./document.pdf"                     # Add local file (PDF, text, Markdown, Word)
notebooklm source list                                     # List all sources in active notebook
notebooklm source get-guide <source_id>                    # Get source summary
notebooklm source get-fulltext <source_id>                 # Get full indexed text
notebooklm source refresh <source_id>                      # Refresh source content
```

Supported source types: YouTube URLs, web URLs, PDF, text, Markdown, Word docs, audio, video, images, Google Drive links.

**Maximum: 50 sources per notebook.**

### Chat / Query (Analysis)

```bash
notebooklm ask "What are the key insights from these videos?"
notebooklm chat "Follow up question..."
```

**Important:** Analysis is done by Google (NotebookLM/Gemini) — saves Claude Code tokens!

### Content Generation (Deliverables)

Each deliverable type has specific CLI flags. The DESCRIPTION (free text) is the most powerful parameter — it guides Gemini's creative output.

#### Infographic
```bash
notebooklm generate infographic "DESCRIPTION" --orientation <landscape|portrait|square> --detail <concise|standard|detailed> --language <en|th|...> --wait
```

#### Video
```bash
notebooklm generate video "DESCRIPTION" --format <explainer|brief> --style <auto|classic|whiteboard|kawaii|anime|watercolor|retro-print|heritage|paper-craft> --language <en|th|...> --wait
```

#### Audio (Podcast)
```bash
notebooklm generate audio "DESCRIPTION" --format <deep-dive|brief|critique|debate> --length <short|default|long> --language <en|th|...> --wait
```

#### Quiz / Flashcards / Slide Deck / Mind Map / Data Table / Report
```bash
notebooklm generate quiz "DESCRIPTION" --wait
notebooklm generate flashcards "DESCRIPTION" --wait
notebooklm generate slide-deck "DESCRIPTION" --wait
notebooklm generate mind-map "DESCRIPTION" --wait
notebooklm generate data-table "DESCRIPTION" --wait
notebooklm generate report "DESCRIPTION" --format <briefing-doc|study-guide|blog-post|custom> --wait
```

**Common flags for all types:**
- `-n, --notebook TEXT` — Notebook ID (uses current if not set)
- `-s, --source TEXT` — Limit to specific source IDs (repeatable)
- `--language TEXT` — Output language (default: from config or 'en')
- `--wait / --no-wait` — Wait for completion
- `--retry N` — Retry N times on rate limit

---

## Creative Director Mode

**CRITICAL: When user requests ANY deliverable, Claude MUST act as a professional creative director.**

Do NOT just run `notebooklm generate infographic` with default options. Instead:

### Step 1: Analyze the Content
- What is the topic/subject?
- What is the audience? (professional, student, general public)
- What is the purpose? (educate, compare, persuade, summarize)
- How complex is the content? (simple overview vs detailed analysis)

### Step 2: Recommend Options + Craft Description

Act as the appropriate professional for each deliverable type:

#### Infographic → Act as Graphic Designer / Information Designer
Think about:
- **Orientation**: Landscape for comparisons/timelines, Portrait for lists/processes, Square for social media
- **Detail level**: Concise for overview, Detailed for data-heavy content
- **Description prompt**: Specify color theme, visual style, layout structure, emphasis points, data visualization approach

Example recommendations:
```
Content: "AI Agent comparison (Claude vs OpenClaw)"
Recommendation:
  --orientation landscape (เพราะเป็นการเปรียบเทียบ 2 ฝั่ง)
  --detail detailed (มีข้อมูลเยอะ)
  --language th
  DESCRIPTION: "Create a side-by-side comparison layout with a modern tech aesthetic. Use a cool blue-to-purple gradient theme. Highlight key differentiators with icons. Include a feature comparison matrix in the center. Use clean sans-serif typography with data callouts for important statistics."
```

#### Video → Act as Videographer / Motion Designer
Think about:
- **Style**: whiteboard for educational, kawaii for fun/casual, classic for professional, watercolor for artistic, anime for storytelling
- **Format**: explainer for teaching concepts, brief for quick overview
- **Description prompt**: Specify pacing, tone, visual metaphors, key scenes, narrative arc

Example recommendations:
```
Content: "How to use Claude Code Skills"
Recommendation:
  --style whiteboard (เพราะเป็น tutorial)
  --format explainer
  --language en
  DESCRIPTION: "Create a step-by-step tutorial feel. Start with the problem (manual workflow), then reveal the solution (skills). Use hand-drawn annotations to emphasize key commands. Maintain an upbeat, encouraging tone. End with a practical workflow diagram."
```

#### Audio (Podcast) → Act as Audio Producer / Editor
Think about:
- **Format**: deep-dive for comprehensive analysis, debate for contrasting views, critique for evaluation, brief for summary
- **Length**: short (5 min), default (10 min), long (20+ min)
- **Description prompt**: Specify tone, focus areas, structure, engagement style

Example recommendations:
```
Content: "Top 5 AI Trends from YouTube Research"
Recommendation:
  --format deep-dive
  --length default
  --language en
  DESCRIPTION: "Create an engaging discussion between two hosts. Open with the most surprising trend to hook listeners. Dedicate roughly equal time to each trend with real examples from the sources. Use a conversational, curious tone — like two tech enthusiasts sharing discoveries over coffee. Close with practical takeaways the listener can act on today."
```

#### Slide Deck → Act as Presentation Designer
Think about:
- **Description prompt**: Specify slide structure, visual hierarchy, key messages per slide, data visualization

Example:
```
DESCRIPTION: "Professional presentation with clean design. Start with executive summary slide. One key insight per slide with supporting data. Use charts for statistics. Include a comparison table slide. End with actionable recommendations. Keep text minimal — bullet points only, no paragraphs."
```

#### Quiz → Act as Educator / Instructional Designer
Think about:
- **Description prompt**: Specify difficulty mix, question types, focus areas

Example:
```
DESCRIPTION: "Mix of multiple choice and true/false questions. 60% conceptual understanding, 40% specific details. Include tricky distractor options that test real comprehension. Add explanations for correct answers."
```

#### Flashcards → Act as Learning Designer
Think about:
- **Description prompt**: Specify card style, content density

Example:
```
DESCRIPTION: "Front: concise question or term. Back: clear explanation with one practical example. Group by topic. Include mnemonics where helpful."
```

#### Report → Act as Technical Writer / Editor
Think about:
- **Format**: briefing-doc for executives, study-guide for learning, blog-post for publishing
- **Description prompt**: Specify structure, depth, audience

Example:
```
DESCRIPTION: "Executive briefing format. Lead with key findings and recommendations. Include data tables for comparisons. Use clear section headers. Limit to 2000 words. Write for a technical audience familiar with AI but not this specific topic."
```

### Step 3: Present Recommendation to User

Format:
```
สำหรับ [deliverable type] เรื่อง "[topic]" แนะนำแบบนี้ครับ:

Options:
  --orientation landscape
  --detail detailed
  --language th

Description:
  "[crafted professional description]"

ใช้แบบนี้เลยไหมครับ? หรืออยากปรับอะไร?
```

### Step 4: Execute After Approval

Once user approves (ได้เลย / ok / ลุย), run the command with all recommended options.

### Auto Mode

If user says "เลือกให้เลย" or "auto" or "ตัดสินใจเลย", skip Step 3 and execute immediately with the professional recommendation.

### Download Deliverables

```bash
notebooklm download audio ./podcast.mp3
notebooklm download video ./overview.mp4
notebooklm download quiz --format markdown ./quiz.md
notebooklm download quiz --format json ./quiz.json
notebooklm download flashcards --format json ./cards.json
notebooklm download flashcards --format markdown ./cards.md
notebooklm download slide-deck ./slides.pdf
notebooklm download infographic ./infographic.png
notebooklm download mind-map ./mindmap.json
notebooklm download data-table ./data.csv
notebooklm download report ./report.md
```

## Primary Workflow: YouTube Research Pipeline

This is the main workflow from the video — combining yt-search + NotebookLM:

### Step 1: Search YouTube for videos
```bash
python3 ~/.claude/skills/yt-search/scripts/search.py "claude code skills" --count 20
```

### Step 2: Create a notebook for the research
```bash
notebooklm create "Research: Claude Code Skills"
```

### Step 3: Add YouTube URLs as sources

**For small batches (1-7 sources):** Add directly
```bash
notebooklm source add "https://youtube.com/watch?v=VIDEO_ID_1"
notebooklm source add "https://youtube.com/watch?v=VIDEO_ID_2"
```

**For large batches (8+ sources):** Add in parallel groups of 7 — much faster, no rate limiting observed
```bash
# Use Claude Code Bash tool: send 7 source add commands as parallel tool calls in one message
# Wait for all 7 to complete, then send the next batch of 7, etc.
notebooklm source add "URL_1"   # run these 7 in parallel
notebooklm source add "URL_2"
notebooklm source add "URL_3"
notebooklm source add "URL_4"
notebooklm source add "URL_5"
notebooklm source add "URL_6"
notebooklm source add "URL_7"
# → then next batch of 7, etc.
```

**Tip:** Sources are processed by NotebookLM (may take 1-2 minutes per source). NotebookLM automatically extracts captions/transcripts from YouTube videos.

### Step 4: Ask questions (analysis)
```bash
notebooklm ask "What are the top 5 Claude Code skills based on these videos?"
notebooklm ask "What are the emerging trends for how these skills are used?"
```

### Step 5: Generate deliverables
```bash
# Infographic
notebooklm generate infographic --orientation landscape
notebooklm download infographic ./output/skills-infographic.png

# Slide deck
notebooklm generate slide-deck
notebooklm download slide-deck ./output/skills-slides.pdf

# Audio podcast
notebooklm generate audio "create an engaging deep-dive discussion" --wait
notebooklm download audio ./output/skills-podcast.mp3

# Study guide
notebooklm generate report --format "study guide"
notebooklm download report ./output/skills-guide.md
```

## Other Workflows

### Document Research
```bash
notebooklm create "Project Research"
notebooklm source add "./report.pdf"
notebooklm source add "https://arxiv.org/paper..."
notebooklm ask "Summarize the key findings"
notebooklm generate report --format "study guide"
notebooklm download report ./study-guide.md
```

### Quick Analysis (One Prompt)
Tell Claude Code in plain language:
> "Search YouTube for 'AI agents 2026', take top 20 results, create a NotebookLM notebook, add all videos as sources, then ask NotebookLM for the top 5 trends and generate an infographic"

Claude Code will execute all steps automatically.

## Key Benefits

- **Free analysis** — NotebookLM (Google/Gemini) does all the heavy lifting, not Claude
- **Token savings** — Only small token cost to send commands, analysis is offsite
- **Rich deliverables** — Audio, video, quiz, flashcards, infographic, slide deck, mind map, report
- **Source-grounded** — Answers are based on actual content, not hallucinated
- **50 sources per notebook** — Massive context window for analysis

## Important Notes

- All analysis is done by Google (NotebookLM) — saves Claude Code tokens
- Add `--wait` flag to generation commands for synchronous operation
- Sources are processed by NotebookLM (may take 1-2 minutes per source)
- Rate limits may apply for heavy usage
- This uses an unofficial API — may change without notice

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `notebooklm: command not found` | Run: `uv tool install "notebooklm-py[browser]"` |
| Authentication expired | Run: `notebooklm login` again |
| Source add fails | Check URL is valid and accessible |
| Generation stuck | Add `--wait` flag or check with `notebooklm list` |
| Playwright/Chromium error | Run: `playwright install chromium` |
| `TargetClosedError` / browser profile lock | See below |

### Browser Profile Lock (`TargetClosedError`)

Happens when another Chrome process has locked the Playwright browser profile.

**Safe fix (only delete the lock):**
```bash
# Find and remove ONLY the SingletonLock file
find ~/Library/Application\ Support/ms-playwright -name "SingletonLock" -delete
```

**DO NOT delete the whole browser profile directory** — that will wipe your NotebookLM auth session, requiring `notebooklm login` again.

**If lock removal doesn't help:** close all Chrome/Chromium windows, then retry.
