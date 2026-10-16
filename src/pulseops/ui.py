"""Look and feel for the dashboard: SVG icons, CSS, and small HTML building blocks.

Kept apart from app.py so app.py only says *what* is on the page.
Icon shapes are from Lucide (https://lucide.dev, ISC licence): 24x24, stroked lines.
"""

import html

ICONS = {
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 '
    '1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "x": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/>'
    '<circle cx="12" cy="12" r="2"/>',
    "server": '<rect x="2" y="2" width="20" height="8" rx="2"/>'
    '<rect x="2" y="14" width="20" height="8" rx="2"/><path d="M6 6h.01"/><path d="M6 18h.01"/>',
    "layers": '<path d="m12 2 10 5-10 5L2 7Z"/><path d="m2 17 10 5 10-5"/>'
    '<path d="m2 12 10 5 10-5"/>',
    "book": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
    '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "rocket": '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 '
    '0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 '
    '7.5-6 11a22.35 22.35 0 0 1-4 2z"/>',
    "pulse": '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
}

# Status -> (label, text colour, background colour)
STATUS = {
    "root": ("Root cause", "#fca5a5", "#450a0a"),
    "affected": ("Degraded", "#fcd34d", "#422006"),
    "ok": ("Operational", "#86efac", "#052e16"),
}

CSS = """
<style>
.block-container, [data-testid="stMainBlockContainer"] {padding-top: 4.5rem; max-width: 1280px;}
#MainMenu, footer {visibility: hidden;}
.po-top {display:flex; align-items:center; justify-content:space-between;
  border-bottom:1px solid #1e293b; padding-bottom:.8rem; margin-bottom:1rem;}
.po-brand {display:flex; align-items:center; gap:.6rem; font-weight:700; font-size:1.25rem;
  color:#f1f5f9;}
.po-crumb {color:#94a3b8; font-size:.85rem; font-weight:400;}
.po-pill {display:inline-flex; align-items:center; gap:.35rem; padding:.2rem .65rem;
  border-radius:999px; font-size:.78rem; font-weight:600;}
.po-tiles {display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:.75rem;
  margin-bottom:1rem;}
@media (max-width: 900px) {.po-tiles {grid-template-columns:repeat(2, minmax(0,1fr));}}
.po-tile {border:1px solid #1e293b; border-radius:10px; padding:.8rem .9rem; background:#111a2e;}
.po-tile-head {display:flex; align-items:center; gap:.4rem; color:#94a3b8; font-size:.75rem;
  text-transform:uppercase; letter-spacing:.04em; font-weight:600;}
.po-tile-value {font-size:1.45rem; font-weight:700; color:#f1f5f9; margin-top:.3rem;}
.po-tile-sub {font-size:.78rem; color:#94a3b8;}
.po-section {display:flex; align-items:center; gap:.45rem; font-weight:650; color:#f1f5f9;
  font-size:1rem; margin:.4rem 0 .5rem;}
.po-table {width:100%; border-collapse:collapse; font-size:.88rem; margin-bottom:1rem;}
.po-table th {text-align:left; color:#94a3b8; font-weight:600; font-size:.75rem;
  text-transform:uppercase; letter-spacing:.04em; border-bottom:1px solid #1e293b;
  padding:.5rem .6rem;}
.po-table td {border-bottom:1px solid #1e293b; padding:.55rem .6rem; color:#e2e8f0;}
.po-dot {display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:.5rem;}
.po-step {display:flex; gap:.7rem; margin:.45rem 0;}
.po-num {flex:none; width:22px; height:22px; border-radius:50%; background:#0c4a6e;
  color:#bae6fd; font-size:.75rem; font-weight:700; display:flex; align-items:center;
  justify-content:center;}
</style>
"""


def icon(name: str, color: str = "currentColor", size: int = 16) -> str:
    """Inline SVG for one icon."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def pill(text: str, fg: str, bg: str, icon_name: str | None = None) -> str:
    inner = (icon(icon_name, fg, 13) if icon_name else "") + html.escape(text)
    return f'<span class="po-pill" style="color:{fg};background:{bg}">{inner}</span>'


def top_bar(incident: str, is_incident: bool) -> str:
    status = (
        pill("Active incident", "#fca5a5", "#450a0a", "alert")
        if is_incident
        else pill("All systems operational", "#86efac", "#052e16", "check")
    )
    return (
        f'<div class="po-top"><div class="po-brand">{icon("pulse", "#38bdf8", 26)}PulseOps'
        f'<span class="po-crumb">/ Incidents / {html.escape(incident)}</span></div>'
        f"{status}</div>"
    )


def tile(icon_name: str, label: str, value: str, sub: str = "", color: str = "#94a3b8") -> str:
    return (
        f'<div class="po-tile"><div class="po-tile-head">{icon(icon_name, color, 14)}'
        f'{html.escape(label)}</div><div class="po-tile-value">{html.escape(value)}</div>'
        f'<div class="po-tile-sub">{html.escape(sub) or "&nbsp;"}</div></div>'
    )


def tiles(items: list[str]) -> str:
    return f'<div class="po-tiles">{"".join(items)}</div>'


def section(icon_name: str, title: str) -> str:
    return f'<div class="po-section">{icon(icon_name, "#38bdf8", 18)}{html.escape(title)}</div>'


def service_table(rows: list[dict]) -> str:
    """rows: service, status (root/affected/ok), calls, anomalies."""
    body = ""
    for row in rows:
        label, fg, bg = STATUS[row["status"]]
        body += (
            f'<tr><td><span class="po-dot" style="background:{fg}"></span>'
            f"<b>{html.escape(row['service'])}</b></td>"
            f"<td>{pill(label, fg, bg)}</td>"
            f"<td>{html.escape(row['calls'])}</td>"
            f"<td>{html.escape(row['anomalies'])}</td></tr>"
        )
    return (
        '<table class="po-table"><thead><tr><th>Service</th><th>Status</th>'
        "<th>Depends on</th><th>Anomalous metrics</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def steps(items: list[str]) -> str:
    """Numbered steps; items may contain simple HTML like <b>."""
    return "".join(
        f'<div class="po-step"><div class="po-num">{n}</div><div>{text}</div></div>'
        for n, text in enumerate(items, start=1)
    )
