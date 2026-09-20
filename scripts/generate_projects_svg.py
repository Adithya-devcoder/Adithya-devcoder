from __future__ import annotations

import json
import math
import textwrap
import xml.sax.saxutils as sx
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "assets" / "data"
OUTPUT = ROOT / "projects.svg"
DATA_OUTPUT = DATA_DIR / "projects.json"

USERNAME = "Adithya-devcoder"

PROJECTS = [
    {
        "name": "SlickTrace",
        "repo": "SlickTrace",
        "description": "Public repository description not set.",
        "updated_at": "2026-09-11T15:33:12Z",
        "stars": 0,
        "languages": {
            "Python": 500739,
            "TypeScript": 69378,
            "Shell": 5019,
            "CSS": 1799,
            "JavaScript": 1029,
            "HTML": 814,
        },
    },
    {
        "name": "UrbanPulse",
        "repo": "UrbanPulse-Smart-India-Hackathon-",
        "description": "Public repository description not set.",
        "updated_at": "2026-09-06T16:22:16Z",
        "stars": 0,
        "languages": {
            "Python": 301765,
            "TypeScript": 187863,
            "JavaScript": 2310,
            "CSS": 986,
            "HTML": 816,
            "Mako": 704,
            "Dockerfile": 541,
        },
    },
    {
        "name": "HealthCare Access",
        "repo": "HealthCare-Access-Inequality-Analysis-and-Planning-System",
        "description": "Data-driven platform for analyzing healthcare accessibility and underserved regions.",
        "updated_at": "2026-05-25T10:13:12Z",
        "stars": 0,
        "languages": {
            "TypeScript": 275152,
            "CSS": 5072,
            "JavaScript": 871,
            "HTML": 835,
        },
    },
    {
        "name": "Ocean",
        "repo": "Ocean",
        "description": "AI-powered platform for oceanographic and biodiversity data insights.",
        "updated_at": "2026-03-18T04:21:21Z",
        "stars": 0,
        "languages": {
            "TypeScript": 231261,
            "Python": 17221,
            "CSS": 2954,
            "JavaScript": 846,
            "HTML": 840,
        },
    },
    {
        "name": "LinkedIn AI Booster",
        "repo": "Linkedin-AI-Booster-Extension",
        "description": "Public repository description not set.",
        "updated_at": "2026-03-29T08:06:29Z",
        "stars": 0,
        "languages": {
            "JavaScript": 68938,
            "CSS": 24861,
            "HTML": 10483,
        },
    },
    {
        "name": "DevCoder Portfolio",
        "repo": "DevCoder-portfolio-website",
        "description": "Public repository description not set.",
        "updated_at": "2026-05-25T10:12:12Z",
        "stars": 0,
        "languages": {
            "TypeScript": 86044,
            "CSS": 9731,
            "JavaScript": 326,
        },
    },
]


COLORS = {
    "Python": "#22D3EE",
    "TypeScript": "#A78BFA",
    "JavaScript": "#10B981",
    "CSS": "#38BDF8",
    "HTML": "#F97316",
    "Shell": "#94A3B8",
    "Mako": "#F59E0B",
    "Dockerfile": "#60A5FA",
}


def esc(value: str) -> str:
    return sx.escape(value, {"'": "&apos;", '"': "&quot;"})


def since(updated_at: str) -> str:
    dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    days = max(0, (now - dt).days)
    if days < 1:
        return "updated today"
    if days < 30:
        return f"updated {days}d ago"
    months = max(1, days // 30)
    return f"updated {months}mo ago"


def language_rows(languages: dict[str, int], limit: int = 3) -> list[tuple[str, int, str]]:
    total = sum(languages.values())
    if total <= 0:
        return [("No language data", 100, "#64748B")]
    rows = []
    for name, count in sorted(languages.items(), key=lambda item: item[1], reverse=True)[:limit]:
        pct = max(1, round(count / total * 100))
        rows.append((name, pct, COLORS.get(name, "#64748B")))
    return rows


def donut(cx: int, cy: int, radius: int, rows: list[tuple[str, int, str]], label: str) -> str:
    circumference = 2 * math.pi * radius
    pieces = [
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#1F2937" stroke-width="9"/>'
    ]
    offset = 0.0
    for _, pct, color in rows:
        length = circumference * pct / 100
        pieces.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" stroke-width="9" '
            f'stroke-linecap="butt" stroke-dasharray="{length:.2f} {circumference - length:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += length
    pieces.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" class="title" font-size="14" fill="#F8FAFC">{esc(label)}</text>')
    return "".join(pieces)


def wrapped_text(text: str, width: int = 58, lines: int = 2) -> list[str]:
    wrapped = textwrap.wrap(text, width=width)
    if len(wrapped) > lines:
        wrapped = wrapped[:lines]
        wrapped[-1] = wrapped[-1].rstrip(" .,") + "..."
    return wrapped or [""]


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip("-_ ") + "..."


def card(project: dict[str, object], x: int, y: int, w: int, h: int, idx: int) -> str:
    name = str(project["name"])
    repo = str(project["repo"])
    desc = str(project["description"])
    stars = int(project["stars"])
    rows = language_rows(project["languages"])  # type: ignore[arg-type]
    main_pct = rows[0][1] if rows else 0
    icon_colors = ["#22D3EE", "#A78BFA", "#10B981", "#38BDF8", "#7C3AED", "#0891B2"]
    icon_color = icon_colors[idx % len(icon_colors)]

    header_repo = truncate(f"{USERNAME}/{repo}", 58)
    desc_lines = wrapped_text(desc)
    lang_legend = []
    for i, (lang, pct, color) in enumerate(rows):
        ly = y + 78 + i * 18
        lang_legend.append(f'<circle cx="{x + w - 184}" cy="{ly}" r="4" fill="{color}"/>')
        lang_legend.append(f'<text x="{x + w - 174}" y="{ly + 4}" class="mono" font-size="11" fill="#CBD5E1">{esc(lang)} {pct}%</text>')

    tags = [row[0] for row in rows[:3]]
    tag_nodes = []
    tx = x + 72
    for tag in tags:
        tw = max(54, 9 * len(tag) + 20)
        tag_nodes.append(f'<rect x="{tx}" y="{y + h - 50}" width="{tw}" height="20" rx="10" fill="#332465" stroke="#7C3AED" stroke-width="1"/>')
        tag_nodes.append(f'<text x="{tx + tw / 2:.1f}" y="{y + h - 36}" text-anchor="middle" class="mono" font-size="10" fill="#C4B5FD">{esc(tag)}</text>')
        tx += tw + 8

    return f'''
<g>
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#0E1728" stroke="#0891B2" stroke-width="1.1"/>
  <rect x="{x}" y="{y}" width="{w}" height="32" rx="10" fill="#0B1323"/>
  <path d="M{x},{y + 32}H{x + w}" stroke="#1E293B" stroke-width="1"/>
  <circle cx="{x + 18}" cy="{y + 16}" r="2.2" fill="#22D3EE"/>
  <text x="{x + 28}" y="{y + 20}" class="mono" font-size="11" fill="#94A3B8">{esc(header_repo)}</text>
  <circle cx="{x + w - 18}" cy="{y + 16}" r="4" fill="#64748B"/>
  <rect x="{x + 22}" y="{y + 52}" width="40" height="40" rx="9" fill="{icon_color}" opacity="0.16" stroke="{icon_color}" stroke-width="2"/>
  <text x="{x + 42}" y="{y + 78}" text-anchor="middle" class="title" font-size="17" fill="{icon_color}">{esc(name[:1].upper())}</text>
  <text x="{x + 72}" y="{y + 67}" class="title" font-size="17" fill="#F8FAFC">{esc(name)}<tspan fill="#22D3EE">_</tspan></text>
  {''.join(f'<text x="{x + 72}" y="{y + 88 + i * 15}" class="mono" font-size="11" fill="#CBD5E1">{esc(line)}</text>' for i, line in enumerate(desc_lines))}
  {''.join(lang_legend)}
  {donut(x + w - 74, y + 91, 29, rows, str(main_pct) + "%")}
  {''.join(tag_nodes)}
  <text x="{x + 72}" y="{y + h - 14}" class="mono" font-size="10" fill="#22D3EE">★ {stars}</text>
  <text x="{x + 118}" y="{y + h - 14}" class="mono" font-size="10" fill="#64748B">{esc(since(str(project["updated_at"])))}</text>
</g>
'''


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUTPUT.write_text(json.dumps(PROJECTS, indent=2), encoding="utf-8")

    width, height = 1180, 650
    card_w, card_h = 560, 148
    x_positions = [58, 562]
    y_positions = [100, 264, 428]

    cards = []
    for idx, project in enumerate(PROJECTS):
        x = x_positions[idx % 2]
        y = y_positions[idx // 2]
        cards.append(card(project, x, y, card_w, card_h, idx))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Projects list for Adithya Sunderrajan">
<defs>
  <style>
    .mono {{ font-family: "JetBrains Mono", "Fira Code", Consolas, monospace; }}
    .title {{ font-family: "JetBrains Mono", "Fira Code", Consolas, monospace; font-weight: 700; }}
  </style>
</defs>
<rect width="{width}" height="{height}" fill="#090E16"/>
<rect x="24" y="24" width="1132" height="594" rx="0" fill="#0B1323"/>
<text x="54" y="58" class="mono" font-size="13" fill="#22D3EE" letter-spacing="3">PROJECTS.LIST</text>
<text x="184" y="58" class="mono" font-size="11" fill="#64748B">./projects.sh --all</text>
<path d="M54 76H1126" stroke="#1E293B" stroke-width="1"/>
{''.join(cards)}
</svg>
'''
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    print(f"wrote {DATA_OUTPUT} ({DATA_OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
