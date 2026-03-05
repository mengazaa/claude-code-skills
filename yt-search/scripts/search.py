#!/usr/bin/env python3
"""YouTube search via yt-dlp with structured output and views/subs ratio.

Uses --print mode for fast results (10x faster than --dump-json).
"""

import io
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

# Force UTF-8 output on Windows to handle emoji in video titles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Field separator for --print mode (unlikely to appear in video data)
SEP = "|||"

# Fields to extract from yt-dlp
PRINT_FIELDS = [
    "%(id)s",
    "%(title)s",
    "%(channel)s",
    "%(upload_date)s",
    "%(view_count)s",
    "%(duration_string)s",
    "%(channel_follower_count)s",
    "%(description)j",
    "%(tags)j",
    "%(categories)j",
]


def parse_date(date_str):
    """Parse flexible date string into YYYYMMDD format.

    Supports: YYYY-MM-DD, YYYY-MM, "feb 2026", "february 2026", "2026-02", etc.
    """
    import calendar
    date_str = date_str.strip().lower()

    # Try YYYY-MM-DD
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y%m%d")
    except ValueError:
        pass

    # Try YYYY-MM
    try:
        dt = datetime.strptime(date_str, "%Y-%m")
        return dt.strftime("%Y%m%d")
    except ValueError:
        pass

    # Try "feb 2026" or "february 2026"
    for fmt in ("%b %Y", "%B %Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y%m%d")
        except ValueError:
            pass

    # Try "2026 feb" or "2026 february"
    for fmt in ("%Y %b", "%Y %B"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y%m%d")
        except ValueError:
            pass

    print(f"Error: Cannot parse date '{date_str}'. Use formats like: 2026-02, feb 2026, 2026-02-15", file=sys.stderr)
    sys.exit(1)


def get_end_of_month(date_str):
    """Get last day of month from a YYYYMMDD string."""
    import calendar
    year = int(date_str[:4])
    month = int(date_str[4:6])
    last_day = calendar.monthrange(year, month)[1]
    return f"{year}{month:02d}{last_day:02d}"


def parse_args(argv):
    """Parse query and flags from argv."""
    args = argv[1:]
    count = 20
    months = 6
    after_date = None
    before_date = None
    json_output = False
    urls_only = False
    browser = "chrome"  # Default: use Chrome cookies to avoid YouTube bot detection
    query_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--count" and i + 1 < len(args):
            try:
                count = int(args[i + 1])
            except ValueError:
                print(f"Error: --count requires an integer, got '{args[i + 1]}'", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--months" and i + 1 < len(args):
            try:
                months = int(args[i + 1])
            except ValueError:
                print(f"Error: --months requires an integer, got '{args[i + 1]}'", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--after" and i + 1 < len(args):
            after_date = parse_date(args[i + 1])
            months = 0
            i += 2
        elif args[i] == "--before" and i + 1 < len(args):
            before_date = parse_date(args[i + 1])
            months = 0
            i += 2
        elif args[i] == "--within" and i + 1 < len(args):
            parsed = parse_date(args[i + 1])
            after_date = parsed
            before_date = get_end_of_month(parsed)
            months = 0
            i += 2
        elif args[i] == "--no-date-filter":
            months = 0
            i += 1
        elif args[i] == "--json":
            json_output = True
            i += 1
        elif args[i] == "--urls-only":
            urls_only = True
            i += 1
        elif args[i] == "--cookies-from-browser" and i + 1 < len(args):
            browser = args[i + 1]
            i += 2
        elif args[i] == "--no-cookies":
            browser = None
            i += 1
        else:
            query_parts.append(args[i])
            i += 1
    query = " ".join(query_parts)
    if not query:
        print("Usage: search.py <query> [--count N] [--months N] [--after DATE] [--before DATE] [--within MONTH] [--json] [--urls-only] [--cookies-from-browser BROWSER]", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print('  search.py claude code --count 10 --within "feb 2026"', file=sys.stderr)
        print('  search.py AI agents --after 2026-01-01 --before 2026-03-01', file=sys.stderr)
        print('  search.py react tutorial --count 5 --months 3', file=sys.stderr)
        print('  search.py OpenClaw --count 50 --urls-only   # pipe to notebooklm', file=sys.stderr)
        sys.exit(1)
    return query, count, months, json_output, urls_only, browser, after_date, before_date


def safe_int(val):
    """Convert string to int, return None if not possible."""
    if val is None or val == "NA" or val == "None" or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def format_subscribers(n):
    """Format subscriber count as human-readable (e.g., 45.2K, 1.2M)."""
    if n is None:
        return "N/A"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_views(n):
    """Format view count with commas."""
    if n is None:
        return "N/A"
    return f"{n:,}"


def format_date(raw):
    """Convert YYYYMMDD to human-readable date (e.g., Jan 10, 2026)."""
    if not raw or len(raw) != 8 or raw == "NA":
        return "N/A"
    try:
        dt = datetime.strptime(raw, "%Y%m%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"


def get_cutoff_date(months):
    """Get the cutoff date as YYYYMMDD string, N months ago from today."""
    if months <= 0:
        return None
    cutoff = datetime.now() - timedelta(days=months * 30)
    return cutoff.strftime("%Y%m%d")


def safe_json_loads(val, default=""):
    """Load a JSON-encoded value, return default if it fails."""
    if not val or val == "NA" or val == "None":
        return default
    try:
        return json.loads(val)
    except (json.JSONDecodeError, ValueError):
        return val


def parse_print_line(line):
    """Parse a --print output line into a video dict."""
    parts = line.split(SEP)
    if len(parts) < 7:
        return None

    # Fields 7-9 use %(field)j (JSON format) to escape newlines
    desc_raw = safe_json_loads(parts[7].strip(), "") if len(parts) > 7 else ""
    tags_raw = safe_json_loads(parts[8].strip(), []) if len(parts) > 8 else []
    cats_raw = safe_json_loads(parts[9].strip(), []) if len(parts) > 9 else []

    # Normalize: description truncated, tags/categories as comma-separated strings
    description = desc_raw[:500] if isinstance(desc_raw, str) else str(desc_raw)[:500]
    tags = ", ".join(tags_raw) if isinstance(tags_raw, list) else str(tags_raw)
    categories = ", ".join(cats_raw) if isinstance(cats_raw, list) else str(cats_raw)

    return {
        "id": parts[0].strip(),
        "title": parts[1].strip(),
        "channel": parts[2].strip(),
        "upload_date": parts[3].strip(),
        "view_count": safe_int(parts[4].strip()),
        "duration_string": parts[5].strip(),
        "channel_follower_count": safe_int(parts[6].strip()),
        "description": description,
        "tags": tags,
        "categories": categories,
    }


def _run_search(cmd, browser):
    """Run yt-dlp search with auto-retry: if cookies cause timeout, retry without."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result
    except subprocess.TimeoutExpired:
        if browser:
            # Remove cookies flags and retry
            retry_cmd = [a for a in cmd if a not in ("--cookies-from-browser", browser)]
            print(f"Timed out with {browser} cookies. Retrying without cookies...\n", file=sys.stderr)
            try:
                result = subprocess.run(retry_cmd, capture_output=True, text=True, timeout=300)
                return result
            except subprocess.TimeoutExpired:
                print("Error: Search timed out after retry without cookies.", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: Search timed out after 300 seconds.", file=sys.stderr)
            sys.exit(1)


def main():
    query, count, months, json_output, urls_only, browser, after_date, before_date = parse_args(sys.argv)

    if not shutil.which("yt-dlp"):
        print("Error: yt-dlp not found on PATH. Install with: pip install yt-dlp", file=sys.stderr)
        sys.exit(1)

    # Fetch extra results to account for date filtering
    has_date_filter = months > 0 or after_date or before_date
    fetch_count = count * 2 if has_date_filter else count
    search_query = f"ytsearch{fetch_count}:{query}"

    # Use --print for fast output (10x faster than --dump-json)
    print_template = SEP.join(PRINT_FIELDS)
    cmd = [
        "yt-dlp",
        search_query,
        "--print", print_template,
        "--no-download",
        "--no-warnings",
    ]

    if browser:
        cmd.extend(["--cookies-from-browser", browser])

    # Build date label for display
    if after_date and before_date:
        date_label = f", {format_date(after_date)} - {format_date(before_date)}"
    elif after_date:
        date_label = f", after {format_date(after_date)}"
    elif before_date:
        date_label = f", before {format_date(before_date)}"
    elif months > 0:
        date_label = f", last {months} months"
    else:
        date_label = ""
    if has_date_filter:
        print(f"Searching YouTube for: \"{query}\" (top {count} results{date_label})...", file=sys.stderr)
        print(f"(Note: date filter fetches {fetch_count} results then filters — may be slower)\n", file=sys.stderr)
    else:
        print(f"Searching YouTube for: \"{query}\" (top {count} results{date_label})...\n", file=sys.stderr)

    result = _run_search(cmd, browser)

    if result.returncode != 0 and not result.stdout.strip():
        print(f"Error: yt-dlp failed:\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        video = parse_print_line(line)
        if video:
            videos.append(video)

    if not videos:
        print("No results found.", file=sys.stderr)
        sys.exit(0)

    # Apply date filter
    if after_date or before_date:
        filtered = videos
        if after_date:
            filtered = [v for v in filtered if (v["upload_date"] or "00000000") >= after_date]
        if before_date:
            filtered = [v for v in filtered if (v["upload_date"] or "99999999") <= before_date]
        skipped = len(videos) - len(filtered)
        videos = filtered
        if skipped > 0:
            print(f"(Filtered out {skipped} video(s) outside date range)\n", file=sys.stderr)
    else:
        cutoff = get_cutoff_date(months)
        if cutoff:
            filtered = [v for v in videos if (v["upload_date"] or "00000000") >= cutoff]
            skipped = len(videos) - len(filtered)
            videos = filtered
            if skipped > 0:
                print(f"(Filtered out {skipped} video(s) older than {months} months)\n", file=sys.stderr)

    if not videos:
        print("No results found matching date criteria.", file=sys.stderr)
        sys.exit(0)

    # Limit to requested count
    videos = videos[:count]

    # URLs-only mode (for piping to notebooklm source add)
    if urls_only:
        for v in videos:
            vid = v["id"]
            if vid:
                print(f"https://youtube.com/watch?v={vid}")
        return

    # JSON output mode
    if json_output:
        output = []
        for v in videos:
            vid = v["id"]
            output.append({
                "title": v["title"] or "Unknown",
                "channel": v["channel"] or "Unknown",
                "views": v["view_count"],
                "subscribers": v["channel_follower_count"],
                "duration": v["duration_string"],
                "date": format_date(v["upload_date"]),
                "url": f"https://youtube.com/watch?v={vid}" if vid else "N/A",
                "description": v["description"][:200] if v["description"] else "",
                "tags": v["tags"],
                "categories": v["categories"],
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Human-readable output
    divider = "\u2500" * 60

    for i, v in enumerate(videos, 1):
        vid = v["id"]
        views = v["view_count"]
        subs = v["channel_follower_count"]
        url = f"https://youtube.com/watch?v={vid}" if vid else "N/A"

        if subs and views and subs > 0:
            ratio_str = f"{views / subs:.2f}x"
        else:
            ratio_str = "N/A"

        views_str = format_views(views)
        subs_str = format_subscribers(subs)
        meta = f"{v['channel']} ({subs_str} subs)  \u00b7  {views_str} views  \u00b7  {v['duration_string']}  \u00b7  {format_date(v['upload_date'])}"

        print(divider)
        print(f" {i:>2}. {v['title']}")
        print(f"     {meta}")
        print(f"     {url}")

    print(divider)


if __name__ == "__main__":
    main()
