from __future__ import annotations

import math
import textwrap
import xml.sax.saxutils as sx
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "projects"

PROJECTS = [
    {
        "slug": "slicktrace",
        "title": "SlickTrace",
        "repo": "SlickTrace",
        "description": "Python-first public repository with TypeScript support.",
        "stars": 0,
        "updated": "updated Sep 2026",
        "languages": [("Python", 87, "#22D3EE"), ("TypeScript", 12, "#A78BFA"), ("Shell", 1, "#94A3B8")],
    },
    {
        "slug": "urbanpulse",
        "title": "UrbanPulse",
        "repo": "UrbanPulse-Smart-India-Hackathon-",
        "description": "Smart India Hackathon public repository.",
        "stars": 0,
        "updated": "updated Sep 2026",
        "languages": [("Python", 61, "#22D3EE"), ("TypeScript", 38, "#A78BFA"), ("JavaScript", 1, "#10B981")],
    },
    {
        "slug": "healthcare-access",
        "title": "HealthCare Access",
        "repo": "HealthCare-Access-Inequality-Analysis-and-Planning-System",
        "description": "Data-driven platform for healthcare accessibility analysis.",
        "stars": 0,
        "updated": "updated May 2026",
        "languages": [("TypeScript", 98, "#A78BFA"), ("CSS", 2, "#38BDF8"), ("JavaScript", 1, "#10B981")],
    },
    {
        "slug": "ocean",
        "title": "Ocean",
        "repo": "Ocean",
        "description": "AI-powered oceanographic and biodiversity data insights.",
        "stars": 0,
        "updated": "updated Mar 2026",
        "languages": [("TypeScript", 91, "#A78BFA"), ("Python", 7, "#22D3EE"), ("CSS", 1, "#38BDF8")],
    },
    {
        "slug": "linkedin-ai-booster",
        "title": "LinkedIn AI Booster",
        "repo": "Linkedin-AI-Booster-Extension",
        "description": "Browser-extension style public repository.",
        "stars": 0,
        "updated": "updated Mar 2026",
        "languages": [("JavaScript", 66, "#10B981"), ("CSS", 24, "#38BDF8"), ("HTML", 10, "#F97316")],
    },
    {
        "slug": "devcoder-portfolio",
        "title": "DevCoder Portfolio",
        "repo": "DevCoder-portfolio-website",
        "description": "TypeScript portfolio website public repository.",
        "stars": 0,
        "updated": "updated May 2026",
        "languages": [("TypeScript", 90, "#A78BFA"), ("CSS", 10, "#38BDF8"), ("JavaScript", 1, "#10B981")],
    },
]


def esc(value: str) -> str:
    return sx.escape(value, {"'": "&apos;", '"': "&quot;"})


def truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip("-_ ") + "..."


def wrap(value: str, width: int, lines: int) -> list[str]:
    wrapped = textwrap.wrap(value, width=width)
    if len(wrapped) > lines:
        wrapped = wrapped[:lines]
        wrapped[-1] = wrapped[-1].rstrip(" .,") + "..."
    return wrapped or [""]


def donut(cx: int, cy: int, radius: int, languages: list[tuple[str, int, str]]) -> str:
    circumference = 2 * math.pi * radius
    offset = 0.0
    pieces = [f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#1F2937" stroke-width="9"/>']
    for _, pct, color in languages:
        length = circumference * pct / 100
        pieces.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" stroke-width="9" '
            f'stroke-dasharray="{length:.2f} {circumference - length:.2f}" stroke-dashoffset="{-offset:.2f}" '
            f'transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += length
    pieces.append(f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" class="title" font-size="14" fill="#F8FAFC">{languages[0][1]}%</text>')
    return "".join(pieces)


def card(project: dict[str, object], index: int) -> str:
    width, height = 560, 170
    accent = ["#22D3EE", "#A78BFA", "#10B981", "#38BDF8", "#7C3AED", "#0891B2"][index % 6]
    title = str(project["title"])
    repo = str(project["repo"])
    description = str(project["description"])
    languages = project["languages"]  # type: ignore[assignment]
    assert isinstance(languages, list)
    header = truncate(f"Adithya-devcoder/{repo}", 56)
    description_lines = wrap(description, 54, 2)

    legend = []
    for i, (name, pct, color) in enumerate(languages):
        y = 76 + i * 18
        legend.append(f'<circle cx="350" cy="{y}" r="4" fill="{color}"/>')
        legend.append(f'<text x="361" y="{y + 4}" class="mono" font-size="10.5" fill="#CBD5E1">{esc(name)} {pct}%</text>')

    tags = []
    x = 73
    for name, _, _ in languages:
        tw = max(56, len(name) * 8 + 20)
        tags.append(f'<rect x="{x}" y="122" width="{tw}" height="21" rx="10" fill="#332465" stroke="#7C3AED" stroke-width="1"/>')
        tags.append(f'<text x="{x + tw / 2:.1f}" y="136" text-anchor="middle" class="mono" font-size="10" fill="#C4B5FD">{esc(name)}</text>')
        x += tw + 8

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)} project card">
<defs>
  <style>
    .mono {{ font-family: "JetBrains Mono", "Fira Code", Consolas, monospace; }}
    .title {{ font-family: "JetBrains Mono", "Fira Code", Consolas, monospace; font-weight: 700; }}
  </style>
</defs>
<rect width="{width}" height="{height}" rx="10" fill="#0E1728" stroke="#0891B2" stroke-width="1.2"/>
<rect width="{width}" height="34" rx="10" fill="#0B1323"/>
<path d="M0 34H{width}" stroke="#1E293B" stroke-width="1"/>
<circle cx="20" cy="17" r="2.2" fill="#22D3EE"/>
<text x="31" y="21" class="mono" font-size="11" fill="#94A3B8">{esc(header)}</text>
<circle cx="542" cy="17" r="4" fill="#64748B"/>
<rect x="22" y="55" width="40" height="40" rx="9" fill="{accent}" opacity="0.16" stroke="{accent}" stroke-width="2"/>
<text x="42" y="81" text-anchor="middle" class="title" font-size="17" fill="{accent}">{esc(title[:1].upper())}</text>
<text x="73" y="67" class="title" font-size="17" fill="#F8FAFC">{esc(title)}<tspan fill="#22D3EE">_</tspan></text>
{''.join(f'<text x="73" y="{88 + i * 15}" class="mono" font-size="11" fill="#CBD5E1">{esc(line)}</text>' for i, line in enumerate(description_lines))}
{''.join(legend)}
{donut(516, 91, 27, languages)}
{''.join(tags)}
<text x="73" y="158" class="mono" font-size="10" fill="#22D3EE">★ {project["stars"]}</text>
<text x="119" y="158" class="mono" font-size="10" fill="#64748B">{esc(str(project["updated"]))}</text>
</svg>
'''


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for index, project in enumerate(PROJECTS):
        output = OUT_DIR / f'{project["slug"]}.svg'
        output.write_text(card(project, index), encoding="utf-8")
        print(output)


if __name__ == "__main__":
    main()
