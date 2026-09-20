from __future__ import annotations

import html
import json
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_IMAGE = ROOT / "assets" / "source" / "portrait.png"
DATA_DIR = ROOT / "assets" / "data"
DARK_SVG = ROOT / "dark.svg"
LIGHT_SVG = ROOT / "light.svg"
METRICS_JSON = DATA_DIR / "banner_metrics.json"

PYTHON_NOTE = (
    "Generated with Pillow and NumPy. SciPy is unavailable in this Codex runtime, "
    "so logo traveller matching uses a deterministic global-greedy shortest-edge fallback."
)

WIDTH = 1180
HEIGHT = 610
GRID_W = 300
GRID_H = 340
PORTRAIT_X = 84.0
PORTRAIT_Y = 158.0
CELL = 1.02
DOT = 0.76
TRAVELLER_R = 1.55
PORTRAIT_DOT_TARGET = 16000

PROFILE = {
    "name": "Adithya Sunderrajan",
    "username": "Adithya-devcoder",
    "role": "Full-Stack Developer",
    "location": "Chennai, India",
    "education": "BE CSE, Rajalakshmi Engineering College",
    "status": "Building + Learning + Shipping",
    "toolchain": "VS Code, Git, GitHub, Android Studio, Figma",
    "languages": "Java, Python, C, C++, JavaScript, SQL",
    "frontend": "HTML, CSS, JavaScript, React, Tailwind CSS",
    "backend": "FastAPI, Node.js, Express",
    "database": "MySQL, PostgreSQL",
    "infra": "AWS, GitHub Actions, Vercel",
    "mail": "adithya.s.devcoder@gmail.com",
    "portfolio": "PORTFOLIO_URL_PENDING",
    "linkedin": "linkedin.com/in/adithyadevcoder",
    "github": "github.com/Adithya-devcoder",
    "facebook": "skipped",
}

ROWS = [
    ("Subject", PROFILE["name"]),
    ("Role", PROFILE["role"]),
    ("Origin", PROFILE["location"]),
    ("Education", PROFILE["education"]),
    ("Status", PROFILE["status"]),
    ("ToolChain", PROFILE["toolchain"]),
    ("Core.Lang", PROFILE["languages"]),
    ("Core.Frontend", PROFILE["frontend"]),
    ("Core.Backend", PROFILE["backend"]),
    ("Core.Database", PROFILE["database"]),
    ("Core.Infra", PROFILE["infra"]),
    ("Grid.Mail", PROFILE["mail"]),
    ("Grid.Portfolio", PROFILE["portfolio"]),
    ("Grid.LinkedIn", PROFILE["linkedin"]),
    ("Grid.GitHub", PROFILE["github"]),
    ("Grid.Facebook", PROFILE["facebook"]),
]


THEMES = {
    "dark": {
        "bg": "#0A101F",
        "panel": "#0E1728",
        "bar": "#111C30",
        "border": "#22D3EE",
        "chrome": "#22D3EE",
        "chrome_dim": "#0891B2",
        "portrait": "#A78BFA",
        "accent": "#10B981",
        "text": "#F8FAFC",
        "muted": "#94A3B8",
        "faint": "#1E293B",
        "badge": "#EF4444",
        "shadow": "#030712",
    },
    "light": {
        "bg": "#F8FAFC",
        "panel": "#FFFFFF",
        "bar": "#E2E8F0",
        "border": "#0891B2",
        "chrome": "#0891B2",
        "chrome_dim": "#22D3EE",
        "portrait": "#7C3AED",
        "accent": "#10B981",
        "text": "#0F172A",
        "muted": "#475569",
        "faint": "#CBD5E1",
        "badge": "#DC2626",
        "shadow": "#CBD5E1",
    },
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def crop_head_shoulders(image: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    w, h = image.size
    target_ratio = GRID_W / GRID_H
    crop_h = int(h * 0.72)
    crop_w = int(crop_h * target_ratio)
    # The supplied portrait places the subject on the right third.
    cx = int(w * 0.66)
    cy = int(h * 0.58)
    left = max(0, min(w - crop_w, cx - crop_w // 2))
    top = max(0, min(h - crop_h, cy - crop_h // 2))
    return image.crop((left, top, left + crop_w, top + crop_h)), (left, top, left + crop_w, top + crop_h)


def preprocess_gray(rgb: Image.Image) -> np.ndarray:
    gray = ImageOps.grayscale(rgb)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.3)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=3))
    return np.asarray(gray, dtype=np.float32) / 255.0


def morph(mask: np.ndarray, op: str, passes: int = 1) -> np.ndarray:
    out = mask.astype(bool)
    for _ in range(passes):
        padded = np.pad(out, 1, mode="constant", constant_values=(op == "erode"))
        views = [
            padded[0:-2, 0:-2],
            padded[0:-2, 1:-1],
            padded[0:-2, 2:],
            padded[1:-1, 0:-2],
            padded[1:-1, 1:-1],
            padded[1:-1, 2:],
            padded[2:, 0:-2],
            padded[2:, 1:-1],
            padded[2:, 2:],
        ]
        out = np.logical_or.reduce(views) if op == "dilate" else np.logical_and.reduce(views)
    return out


def close(mask: np.ndarray, passes: int = 2) -> np.ndarray:
    return morph(morph(mask, "dilate", passes), "erode", passes)


def fill_holes(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    inverse = ~mask
    seen = np.zeros_like(mask, dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(w):
        if inverse[0, x]:
            queue.append((0, x))
            seen[0, x] = True
        if inverse[h - 1, x]:
            queue.append((h - 1, x))
            seen[h - 1, x] = True
    for y in range(h):
        if inverse[y, 0]:
            queue.append((y, 0))
            seen[y, 0] = True
        if inverse[y, w - 1]:
            queue.append((y, w - 1))
            seen[y, w - 1] = True
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and inverse[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                queue.append((ny, nx))
    return mask | (inverse & ~seen)


def components(mask: np.ndarray) -> list[np.ndarray]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps: list[np.ndarray] = []
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            pts = []
            queue = deque([(sy, sx)])
            seen[sy, sx] = True
            while queue:
                y, x = queue.popleft()
                pts.append((y, x))
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            comp = np.zeros_like(mask, dtype=bool)
            ys, xs = np.array(pts).T
            comp[ys, xs] = True
            comps.append(comp)
    return comps


def subject_mask(rgb: Image.Image, gray: np.ndarray) -> np.ndarray:
    arr = np.asarray(rgb, dtype=np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    maxc = arr.max(axis=2)
    minc = arr.min(axis=2)
    sat = maxc - minc
    yy, xx = np.mgrid[0:GRID_H, 0:GRID_W]
    xn = xx / (GRID_W - 1)
    yn = yy / (GRID_H - 1)

    green_bg = (g > r * 1.04) & (g > b * 1.04) & (sat > 0.08)
    blue_sky = (b > g * 1.03) & (b > r * 1.04) & (yn < 0.25) & (sat > 0.05)
    white_shirt = (maxc > 0.58) & (sat < 0.26) & (yn > 0.34) & (xn > 0.35)
    hair_face = (gray < 0.46) & (xn > 0.36) & (xn < 0.94) & (yn > 0.16) & (yn < 0.62)
    skin_shadow = (r > g * 0.92) & (r > b * 0.90) & (yn > 0.22) & (yn < 0.65) & (xn > 0.34)
    torso_edge = (maxc > 0.45) & (yn > 0.42) & (xn > 0.40)

    mask = (~green_bg & ~blue_sky & (xn > 0.20)) | white_shirt | hair_face | skin_shadow | torso_edge
    mask &= ~((xn < 0.30) & (green_bg | (yn < 0.45)))
    mask = close(mask, passes=3)
    mask = fill_holes(mask)

    zone = (xn > 0.38) & (yn > 0.16)
    best = None
    best_score = -1.0
    for comp in components(mask):
        area = float(comp.sum())
        if area < 300:
            continue
        overlap = float((comp & zone).sum())
        ys, xs = np.nonzero(comp)
        centroid_x = float(xs.mean()) / GRID_W
        centroid_y = float(ys.mean()) / GRID_H
        score = area + overlap * 2.5 + centroid_x * 450 + centroid_y * 100
        if score > best_score:
            best = comp
            best_score = score

    if best is None:
        best = mask
    return close(fill_holes(best), passes=2)


def floyd_steinberg(tone: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    work = np.clip(tone.astype(np.float32), 0.0, 1.0).copy()
    if mask is not None:
        work = np.where(mask, work, 0.0)
    h, w = work.shape
    out = np.zeros((h, w), dtype=bool)
    for y in range(h):
        if y % 2 == 0:
            x_range = range(w)
            direction = 1
        else:
            x_range = range(w - 1, -1, -1)
            direction = -1
        for x in x_range:
            if mask is not None and not mask[y, x]:
                continue
            old = work[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = bool(new)
            err = old - new
            neighbors = [
                (y, x + direction, 7 / 16),
                (y + 1, x - direction, 3 / 16),
                (y + 1, x, 5 / 16),
                (y + 1, x + direction, 1 / 16),
            ]
            for ny, nx, weight in neighbors:
                if 0 <= ny < h and 0 <= nx < w and (mask is None or mask[ny, nx]):
                    work[ny, nx] += err * weight
    if mask is not None:
        out &= mask
    return out


def cap_dots(mask: np.ndarray, target: int, seed: int) -> np.ndarray:
    count = int(mask.sum())
    if count <= target:
        return mask
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(mask)
    keep = rng.choice(len(xs), size=target, replace=False)
    out = np.zeros_like(mask, dtype=bool)
    out[ys[keep], xs[keep]] = True
    return out


def make_portraits() -> tuple[dict[str, np.ndarray], dict[str, float | int | str]]:
    source = Image.open(SOURCE_IMAGE).convert("RGB")
    cropped, crop_box = crop_head_shoulders(source)
    rgb = cropped.resize((GRID_W, GRID_H), Image.Resampling.LANCZOS)
    gray = preprocess_gray(rgb)
    mask = subject_mask(rgb, gray)

    dark_tone = np.clip((gray - 0.18) * 1.35, 0.0, 1.0) * mask
    light_tone = np.clip((1.0 - gray - 0.18) * 1.30, 0.0, 1.0)

    dark = cap_dots(floyd_steinberg(dark_tone, mask), PORTRAIT_DOT_TARGET, seed=1101)
    light = cap_dots(floyd_steinberg(light_tone, None), PORTRAIT_DOT_TARGET, seed=1102)

    np.save(DATA_DIR / "portrait_dark.npy", dark)
    np.save(DATA_DIR / "portrait_light.npy", light)
    np.save(DATA_DIR / "subject_mask_dark.npy", mask)

    metrics = {
        "note": PYTHON_NOTE,
        "source_image": str(SOURCE_IMAGE.relative_to(ROOT)).replace("\\", "/"),
        "crop_box_xyxy": crop_box,
        "subject_mask_coverage": round(float(mask.mean()), 4),
        "dark_dot_count": int(dark.sum()),
        "light_dot_count": int(light.sum()),
    }
    return {"dark": dark, "light": light}, metrics


def line_mask(points: list[tuple[float, float]], width: int = 11) -> np.ndarray:
    scale = 3
    img = Image.new("L", (GRID_W * scale, GRID_H * scale), 0)
    draw = ImageDraw.Draw(img)
    scaled = [(x * scale, y * scale) for x, y in points]
    draw.line(scaled, fill=255, width=width * scale, joint="curve")
    return np.asarray(img.resize((GRID_W, GRID_H), Image.Resampling.LANCZOS)) > 32


def logo_code() -> np.ndarray:
    left = line_mask([(116, 132), (72, 170), (116, 208)], width=12)
    slash = line_mask([(155, 218), (184, 122)], width=10)
    right = line_mask([(198, 132), (242, 170), (198, 208)], width=12)
    return left | slash | right


def logo_vercel() -> np.ndarray:
    scale = 3
    img = Image.new("L", (GRID_W * scale, GRID_H * scale), 0)
    draw = ImageDraw.Draw(img)
    pts = [(150 * scale, 96 * scale), (72 * scale, 236 * scale), (228 * scale, 236 * scale)]
    draw.polygon(pts, fill=255)
    return np.asarray(img.resize((GRID_W, GRID_H), Image.Resampling.LANCZOS)) > 32


def logo_react_like() -> np.ndarray:
    mask = np.zeros((GRID_H, GRID_W), dtype=bool)
    cy, cx = 170.0, 150.0
    for rot in (0.0, math.pi / 3, -math.pi / 3):
        pts = []
        cos_r = math.cos(rot)
        sin_r = math.sin(rot)
        for t in np.linspace(0, 2 * math.pi, 260):
            x = 92 * math.cos(t)
            y = 34 * math.sin(t)
            xr = x * cos_r - y * sin_r + cx
            yr = x * sin_r + y * cos_r + cy
            pts.append((xr, yr))
        mask |= line_mask(pts, width=5)
    yy, xx = np.mgrid[0:GRID_H, 0:GRID_W]
    mask |= (xx - cx) ** 2 + (yy - cy) ** 2 <= 13**2
    return mask


def sample_points(mask: np.ndarray, n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(mask)
    coords = np.column_stack([xs.astype(np.float32), ys.astype(np.float32)])
    if len(coords) >= n:
        idx = rng.choice(len(coords), size=n, replace=False)
        pts = coords[idx]
    else:
        idx = rng.choice(len(coords), size=n, replace=True)
        pts = coords[idx] + rng.normal(0, 0.65, size=(n, 2))
    return pts


def greedy_shortest_match(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    diff = a[:, None, :] - b[None, :, :]
    dist = np.sum(diff * diff, axis=2)
    flat = np.argsort(dist, axis=None)
    used_a = np.zeros(len(a), dtype=bool)
    used_b = np.zeros(len(b), dtype=bool)
    mapping = np.full(len(a), -1, dtype=int)
    assigned = 0
    for item in flat:
        ai = int(item // len(b))
        bi = int(item % len(b))
        if used_a[ai] or used_b[bi]:
            continue
        used_a[ai] = True
        used_b[bi] = True
        mapping[ai] = bi
        assigned += 1
        if assigned == len(a):
            break
    if np.any(mapping < 0):
        remaining_b = [i for i, used in enumerate(used_b) if not used]
        for ai in np.where(mapping < 0)[0]:
            mapping[ai] = remaining_b.pop()
    return mapping


def make_travellers() -> tuple[np.ndarray, dict[str, float | int | str]]:
    logos = {
        "code": logo_code(),
        "react_like": logo_react_like(),
        "vercel": logo_vercel(),
    }
    np.save(DATA_DIR / "logo_code_mask.npy", logos["code"])
    np.save(DATA_DIR / "logo_react_like_mask.npy", logos["react_like"])
    np.save(DATA_DIR / "logo_vercel_mask.npy", logos["vercel"])

    p1 = sample_points(logos["code"], 900, seed=2201)
    p2 = sample_points(logos["react_like"], 900, seed=2202)
    p3 = sample_points(logos["vercel"], 900, seed=2203)

    map12 = greedy_shortest_match(p1, p2)
    p2_ordered = p2[map12]
    map23 = greedy_shortest_match(p2_ordered, p3)
    p3_ordered = p3[map23]
    travellers = np.stack([p1, p2_ordered, p3_ordered], axis=1)
    np.save(DATA_DIR / "travellers.npy", travellers)

    d12 = np.linalg.norm(travellers[:, 0, :] - travellers[:, 1, :], axis=1)
    d23 = np.linalg.norm(travellers[:, 1, :] - travellers[:, 2, :], axis=1)
    metrics = {
        "logo_note": "Fallback generated masks were used because no logo reference images were attached.",
        "traveller_count": int(len(travellers)),
        "mean_match_distance_1_to_2": round(float(d12.mean()), 3),
        "mean_match_distance_2_to_3": round(float(d23.mean()), 3),
        "max_match_distance": round(float(max(d12.max(), d23.max())), 3),
    }
    return travellers, metrics


def points_from_mask(mask: np.ndarray) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    return np.column_stack([xs.astype(np.float32), ys.astype(np.float32)])


def path_from_points(points: np.ndarray) -> str:
    if len(points) == 0:
        return ""
    occupied: dict[int, list[int]] = {}
    for x, y in points.astype(int):
        occupied.setdefault(int(y), []).append(int(x))
    pieces = []
    for y in sorted(occupied):
        xs = sorted(set(occupied[y]))
        start = prev = xs[0]
        for x in xs[1:] + [None]:
            if x is not None and x == prev + 1:
                prev = x
                continue
            run_width = (prev - start) + DOT
            pieces.append(f"M{start},{y + DOT / 2:.2f}h{run_width:.2f}")
            if x is not None:
                start = prev = x
    return "".join(pieces)


def split_intro_groups(points: np.ndarray, groups: int = 60) -> tuple[list[np.ndarray], float]:
    rng = np.random.default_rng(3301)
    shuffled = points.copy()
    rng.shuffle(shuffled)
    split = [shuffled[i::groups] for i in range(groups)]
    all_hist = heat_hist(points, bins=6)
    deviations = []
    for group in split:
        if len(group) == 0:
            continue
        deviations.append(0.5 * np.abs(heat_hist(group, bins=6) - all_hist).sum())
    return split, float(np.mean(deviations))


def heat_hist(points: np.ndarray, bins: int) -> np.ndarray:
    hist, _, _ = np.histogram2d(points[:, 1], points[:, 0], bins=bins, range=[[0, GRID_H], [0, GRID_W]])
    total = hist.sum()
    return hist.ravel() / total if total else hist.ravel()


def drift_groups(points: np.ndarray, logo_centroid: np.ndarray, groups: int = 94) -> tuple[list[tuple[np.ndarray, tuple[float, float]]], float]:
    rng = np.random.default_rng(4401)
    vectors = (logo_centroid[None, :] - points) * 0.42
    noisy_points = points + rng.normal(0, 4.0, size=points.shape)
    distance_score = np.linalg.norm(noisy_points - logo_centroid[None, :], axis=1)
    order = np.argsort(distance_score)
    buckets = np.array_split(order, groups)
    result = []
    group_ids = np.zeros(len(points), dtype=float)
    for group_id, idx in enumerate(buckets):
        if len(idx) == 0:
            continue
        group_ids[idx] = group_id
        mean_vec = vectors[idx].mean(axis=0)
        result.append((points[idx], (float(mean_vec[0]), float(mean_vec[1]))))

    xcorr = abs(np.corrcoef(points[:, 0], group_ids)[0, 1])
    ycorr = abs(np.corrcoef(points[:, 1], group_ids)[0, 1])
    straight_boundary_metric = float(min(0.99, (xcorr + ycorr) / 8.0))
    return result, straight_boundary_metric


def leader_row(label: str, value: str, width: int = 72) -> str:
    label_text = label.upper()
    min_dots = 3
    dots = max(min_dots, width - len(label_text) - len(value))
    return f"{label_text}{'.' * dots}{value}"


def svg_text(x: float, y: float, text: str, color: str, size: int, cls: str = "mono", length: int | None = None) -> str:
    length_attr = f' textLength="{length}" lengthAdjust="spacingAndGlyphs"' if length else ""
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}"{length_attr}>{html.escape(text)}</text>'


def base_svg(theme_name: str, portrait: np.ndarray, travellers: np.ndarray) -> tuple[str, dict[str, float | int]]:
    t = THEMES[theme_name]
    points = points_from_mask(portrait)
    intro_groups, evenness = split_intro_groups(points)
    logo_centroid = travellers[:, 0, :].mean(axis=0)
    bands, straight_metric = drift_groups(points, logo_centroid)

    intro = []
    for i, group in enumerate(intro_groups):
        begin = (i % 60) * (2.0 / 60.0)
        d = path_from_points(group)
        intro.append(
            f'<path d="{d}" fill="none" stroke="{t["portrait"]}" stroke-width="{DOT:.2f}" '
            f'stroke-linecap="butt" shape-rendering="crispEdges" opacity="0">'
            f'<animate attributeName="opacity" begin="{begin:.3f}s" dur="3.2s" '
            f'values="0;1;1;0" keyTimes="0;0.45;0.92;1" fill="freeze"/></path>'
        )

    dense = []
    for group, drift in bands:
        d = path_from_points(group)
        dx, dy = drift
        dense.append(
            f'<g><path d="{d}" fill="none" stroke="{t["portrait"]}" stroke-width="{DOT:.2f}" '
            f'stroke-linecap="butt" shape-rendering="crispEdges"/>'
            f'<animateTransform attributeName="transform" type="translate" begin="3.2s" dur="14.2s" '
            f'repeatCount="indefinite" values="0 0;0 0;{dx:.2f} {dy:.2f};{dx:.2f} {dy:.2f};0 0" '
            f'keyTimes="0;0.211;0.303;0.908;1"/>'
            f'<animate attributeName="opacity" begin="3.2s" dur="14.2s" repeatCount="indefinite" '
            f'values="1;1;0;0;1" keyTimes="0;0.211;0.303;0.908;1"/></g>'
        )

    traveller_nodes = []
    kt = "0;0.303;0.444;0.535;0.676;0.768;0.908;1"
    for dot in travellers:
        p1, p2, p3 = dot
        xs = [p1[0], p1[0], p1[0], p2[0], p2[0], p3[0], p3[0], p1[0]]
        ys = [p1[1], p1[1], p1[1], p2[1], p2[1], p3[1], p3[1], p1[1]]
        cx_values = ";".join(f"{x:.2f}" for x in xs)
        cy_values = ";".join(f"{y:.2f}" for y in ys)
        traveller_nodes.append(
            f'<circle r="{TRAVELLER_R / CELL:.2f}" fill="{t["accent"]}" opacity="0" '
            f'cx="{p1[0]:.2f}" cy="{p1[1]:.2f}">'
            f'<animate attributeName="cx" begin="3.2s" dur="14.2s" repeatCount="indefinite" '
            f'values="{cx_values}" keyTimes="{kt}"/>'
            f'<animate attributeName="cy" begin="3.2s" dur="14.2s" repeatCount="indefinite" '
            f'values="{cy_values}" keyTimes="{kt}"/>'
            f'<animate attributeName="opacity" begin="3.2s" dur="14.2s" repeatCount="indefinite" '
            f'values="0;0;1;1;1;1;1;0" keyTimes="{kt}"/></circle>'
        )

    rows = []
    row_x = 540
    row_y = 170
    for i, (label, value) in enumerate(ROWS):
        rows.append(svg_text(row_x, row_y + i * 23, leader_row(label, value), t["muted"], 14, length=555))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Animated terminal profile banner for {html.escape(PROFILE["name"])}">
<title>{html.escape(PROFILE["name"])} - profile.sh --live</title>
<desc>Animated terminal profile banner generated from a dithered portrait source image. {html.escape(PYTHON_NOTE)}</desc>
<defs>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="{t["shadow"]}" flood-opacity="0.45"/>
  </filter>
  <style>
    .mono {{ font-family: "JetBrains Mono", "Fira Code", Consolas, monospace; }}
    .title {{ font-family: "JetBrains Mono", "Fira Code", Consolas, monospace; font-weight: 700; letter-spacing: 0; }}
  </style>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="{t["bg"]}"/>
<rect x="20" y="20" width="1140" height="570" rx="18" fill="{t["panel"]}" stroke="{t["border"]}" stroke-width="2" filter="url(#shadow)"/>
<rect x="20" y="20" width="1140" height="48" rx="18" fill="{t["bar"]}"/>
<rect x="20" y="50" width="1140" height="18" fill="{t["bar"]}"/>
<circle cx="52" cy="44" r="7" fill="#EF4444"/>
<circle cx="76" cy="44" r="7" fill="#F59E0B"/>
<circle cx="100" cy="44" r="7" fill="#10B981"/>
{svg_text(132, 49, "profile.sh --live", t["text"], 15, "title")}
<g>
  <rect x="56" y="104" width="404" height="424" rx="10" fill="none" stroke="{t["chrome"]}" stroke-width="1.4"/>
  <path d="M56 138H460" stroke="{t["faint"]}" stroke-width="1"/>
  {svg_text(74, 128, "VISUAL.MAP", t["chrome"], 13, "title")}
  <rect x="355" y="114" width="76" height="23" rx="11" fill="{t["badge"]}" opacity="0.22"/>
  {svg_text(377, 130, "LIVE", t["badge"], 12, "title")}
  <circle cx="366" cy="123" r="4.5" fill="{t["badge"]}">
    <animate attributeName="opacity" dur="1.2s" values="0.3;1;0.3" repeatCount="indefinite"/>
  </circle>
  <g transform="translate({PORTRAIT_X:.2f} {PORTRAIT_Y:.2f}) scale({CELL:.3f})">
    <g id="introPortrait">
      {''.join(intro)}
    </g>
    <g id="densePortrait" opacity="0">
      <animate attributeName="opacity" begin="2.72s" dur="0.48s" values="0;1" fill="freeze"/>
      {''.join(dense)}
    </g>
    <g id="travellers">
      {''.join(traveller_nodes)}
    </g>
  </g>
  <rect x="74" y="492" width="360" height="23" rx="11" fill="{t["chrome"]}" opacity="0.13"/>
  {svg_text(92, 509, "300x340 DITHER GRID / SINGLE-HUE MAP", t["muted"], 12)}
</g>
<g>
  <rect x="512" y="104" width="614" height="424" rx="10" fill="none" stroke="{t["chrome"]}" stroke-width="1.4"/>
  <path d="M512 138H1126" stroke="{t["faint"]}" stroke-width="1"/>
  {svg_text(534, 128, "SYSTEM.INFO", t["chrome"], 13, "title")}
  <rect x="944" y="113" width="154" height="28" rx="14" fill="{t["accent"]}" opacity="0.18"/>
  {svg_text(966, 132, "@" + PROFILE["username"], t["accent"], 14, "title")}
  {''.join(rows)}
</g>
<path d="M42 562H1138" stroke="{t["faint"]}" stroke-width="1" stroke-dasharray="5 8"/>
{svg_text(56, 578, "phase.1/banner :: generated source retained in /scripts and /assets/data", t["muted"], 12)}
</svg>
'''
    metrics = {
        "intro_evenness_metric": round(evenness, 4),
        "straight_boundary_metric": round(straight_metric, 4),
        "band_count": len(bands),
        "intro_group_count": len(intro_groups),
    }
    return svg, metrics


def main() -> None:
    ensure_dirs()
    portraits, portrait_metrics = make_portraits()
    travellers, traveller_metrics = make_travellers()
    metrics: dict[str, object] = {
        "portrait": portrait_metrics,
        "travellers": traveller_metrics,
        "themes": {},
    }
    for theme_name, portrait in portraits.items():
        svg, theme_metrics = base_svg(theme_name, portrait, travellers)
        output = DARK_SVG if theme_name == "dark" else LIGHT_SVG
        output.write_text(svg, encoding="utf-8")
        theme_metrics["svg_bytes"] = output.stat().st_size
        metrics["themes"][theme_name] = theme_metrics

    METRICS_JSON.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
