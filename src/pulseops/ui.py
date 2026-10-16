"""Look and feel for the dashboard: SVG icons, CSS, and small HTML building blocks.

Kept apart from app.py so app.py only says *what* is on the page.
Icon shapes are from Lucide (https://lucide.dev, ISC licence): 24x24, stroked lines.
"""

import html

import altair as alt
import pandas as pd

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

# Two palettes. Every colour on the page comes from here, so switching theme is one lookup.
PALETTES = {
    "dark": {
        "bg": "#0b1220",
        "panel": "#111a2e",
        "border": "#1e293b",
        "text": "#e2e8f0",
        "strong": "#f1f5f9",
        "muted": "#94a3b8",
        "accent": "#38bdf8",
        "red": "#fca5a5",
        "red_bg": "#450a0a",
        "amber": "#fcd34d",
        "amber_bg": "#422006",
        "green": "#86efac",
        "green_bg": "#052e16",
        "num_bg": "#0c4a6e",
        "num": "#bae6fd",
    },
    "light": {
        "bg": "#ffffff",
        "panel": "#f8fafc",
        "border": "#e2e8f0",
        "text": "#1e293b",
        "strong": "#0f172a",
        "muted": "#64748b",
        "accent": "#0284c7",
        "red": "#b91c1c",
        "red_bg": "#fee2e2",
        "amber": "#b45309",
        "amber_bg": "#fef3c7",
        "green": "#15803d",
        "green_bg": "#dcfce7",
        "num_bg": "#e0f2fe",
        "num": "#0369a1",
    },
}

# Status -> (label, colour key). The key picks e.g. "red" and "red_bg" from the palette.
STATUS = {
    "root": ("Root cause", "red"),
    "affected": ("Degraded", "amber"),
    "ok": ("Operational", "green"),
}

# Light mode also has to repaint Streamlit's own surfaces, because the base theme
# in .streamlit/config.toml is dark.
LIGHT_OVERRIDES = """
[data-testid="stApp"], [data-testid="stHeader"] {background:#ffffff; color:#1e293b;}
[data-testid="stSidebar"] {background:#f1f5f9;}
[data-testid="stSidebar"] *, [data-testid="stMain"] p, [data-testid="stMain"] li,
[data-testid="stMain"] label, [data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] {color:#1e293b;}
[data-testid="stCaptionContainer"] {opacity:.75;}
[data-baseweb="select"] > div, [data-testid="stNumberInputContainer"],
[data-testid="stNumberInput"] input {background:#ffffff; color:#1e293b;
  border-color:#cbd5e1;}
[data-testid="stExpander"] details, [data-testid="stVerticalBlockBorderWrapper"] {
  background:#ffffff; border-color:#e2e8f0;}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {color:#1e293b;}
[data-testid="stExpander"] summary {background:#f8fafc !important;}
[data-testid="stMain"] code {background:#f1f5f9; color:#0f172a;}
[data-testid="stBaseButton-secondary"] {background:#ffffff; color:#1e293b; border-color:#cbd5e1;}
[data-testid="stBaseButton-primary"] {background:#0284c7; color:#ffffff; border-color:#0284c7;}
[data-testid="stBaseButton-primary"] p {color:#ffffff;}
button[data-baseweb="tab"] p {color:#334155;}
[data-testid="stSelectbox"] div:has(> input), [role="listbox"], [role="option"] {
  background:#ffffff; color:#1e293b;}
[data-testid="stButtonGroup"] button[aria-checked="false"] {background:#ffffff;
  color:#334155; border-color:#cbd5e1;}
"""

CSS_TEMPLATE = """
<style>
.block-container, [data-testid="stMainBlockContainer"] {padding-top: 4.5rem; max-width: 1280px;}
#MainMenu, footer {visibility: hidden;}
.po-top {display:flex; align-items:center; justify-content:space-between;
  border-bottom:1px solid {border}; padding-bottom:.8rem; margin-bottom:1rem;}
.po-brand {display:flex; align-items:center; gap:.6rem; font-weight:700; font-size:1.25rem;
  color:{strong};}
.po-brand svg, .po-section svg {color:{accent};}
.po-crumb {color:{muted}; font-size:.85rem; font-weight:400;}
.po-pill {display:inline-flex; align-items:center; gap:.35rem; padding:.2rem .65rem;
  border-radius:999px; font-size:.78rem; font-weight:600;}
.po-red {color:{red}; background:{red_bg};}
.po-amber {color:{amber}; background:{amber_bg};}
.po-green {color:{green}; background:{green_bg};}
.po-dot.po-red, .po-dot.po-amber, .po-dot.po-green {background:currentColor;}
.po-tiles {display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:.75rem;
  margin-bottom:1rem;}
@media (max-width: 900px) {.po-tiles {grid-template-columns:repeat(2, minmax(0,1fr));}}
.po-tile {border:1px solid {border}; border-radius:10px; padding:.8rem .9rem; background:{panel};}
.po-tile-head {display:flex; align-items:center; gap:.4rem; color:{muted}; font-size:.75rem;
  text-transform:uppercase; letter-spacing:.04em; font-weight:600;}
.po-tile-head.po-red, .po-tile-head.po-green {background:none;}
.po-tile-value {font-size:1.45rem; font-weight:700; color:{strong}; margin-top:.3rem;}
.po-tile-sub {font-size:.78rem; color:{muted};}
.po-section {display:flex; align-items:center; gap:.45rem; font-weight:650; color:{strong};
  font-size:1rem; margin:.4rem 0 .5rem;}
.po-table {width:100%; border-collapse:collapse; font-size:.88rem; margin-bottom:1rem;}
.po-table th {text-align:left; color:{muted}; font-weight:600; font-size:.75rem;
  text-transform:uppercase; letter-spacing:.04em; border-bottom:1px solid {border};
  padding:.5rem .6rem;}
.po-table td {border-bottom:1px solid {border}; padding:.55rem .6rem; color:{text};}
.po-dot {display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:.5rem;}
.po-step {display:flex; gap:.7rem; margin:.45rem 0;}
.po-num {flex:none; width:22px; height:22px; border-radius:50%; background:{num_bg};
  color:{num}; font-size:.75rem; font-weight:700; display:flex; align-items:center;
  justify-content:center;}
{overrides}
</style>
"""


def css(mode: str) -> str:
    """The page's <style> block for "dark" or "light"."""
    style = CSS_TEMPLATE
    for key, value in PALETTES[mode].items():
        style = style.replace("{" + key + "}", value)
    return style.replace("{overrides}", LIGHT_OVERRIDES if mode == "light" else "")


def icon(name: str, size: int = 16) -> str:
    """Inline SVG for one icon. It takes the text colour of whatever it sits in."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def pill(text: str, tone: str, icon_name: str | None = None) -> str:
    """tone: red, amber or green."""
    inner = (icon(icon_name, 13) if icon_name else "") + html.escape(text)
    return f'<span class="po-pill po-{tone}">{inner}</span>'


def top_bar(incident: str, is_incident: bool) -> str:
    status = (
        pill("Active incident", "red", "alert")
        if is_incident
        else pill("All systems operational", "green", "check")
    )
    return (
        f'<div class="po-top"><div class="po-brand">{icon("pulse", 26)}PulseOps'
        f'<span class="po-crumb">/ Incidents / {html.escape(incident)}</span></div>'
        f"{status}</div>"
    )


def tile(icon_name: str, label: str, value: str, sub: str = "", tone: str = "") -> str:
    """One summary card. tone ("red"/"green") colours the label line; empty = grey."""
    tone_class = f" po-{tone}" if tone else ""
    return (
        f'<div class="po-tile"><div class="po-tile-head{tone_class}">{icon(icon_name, 14)}'
        f'{html.escape(label)}</div><div class="po-tile-value">{html.escape(value)}</div>'
        f'<div class="po-tile-sub">{html.escape(sub) or "&nbsp;"}</div></div>'
    )


def tiles(items: list[str]) -> str:
    return f'<div class="po-tiles">{"".join(items)}</div>'


def section(icon_name: str, title: str) -> str:
    return f'<div class="po-section">{icon(icon_name, 18)}{html.escape(title)}</div>'


def service_table(rows: list[dict]) -> str:
    """rows: service, status (root/affected/ok), calls, anomalies."""
    body = ""
    for row in rows:
        label, tone = STATUS[row["status"]]
        body += (
            f'<tr><td><span class="po-dot po-{tone}"></span>'
            f"<b>{html.escape(row['service'])}</b></td>"
            f"<td>{pill(label, tone)}</td>"
            f"<td>{html.escape(row['calls'])}</td>"
            f"<td>{html.escape(row['anomalies'])}</td></tr>"
        )
    return (
        '<table class="po-table"><thead><tr><th>Service</th><th>Status</th>'
        "<th>Depends on</th><th>Anomalous metrics</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def table(rows: list[dict]) -> str:
    """A plain themed table from a list of dicts (keys become the header)."""
    if not rows:
        return ""
    header = "".join(f"<th>{html.escape(str(k))}</th>" for k in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in row.values()) + "</tr>"
        for row in rows
    )
    return f'<table class="po-table"><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>'


def steps(items: list[str]) -> str:
    """Numbered steps; items may contain simple HTML like <b>."""
    return "".join(
        f'<div class="po-step"><div class="po-num">{n}</div><div>{text}</div></div>'
        for n, text in enumerate(items, start=1)
    )


def line_chart(data: pd.DataFrame, y_label: str, mode: str) -> alt.Chart:
    """One line per service over time, coloured to match the current theme.

    `data` has the minute as its index and one column per service.
    """
    p = PALETTES[mode]
    long = data.reset_index(names="minute").melt("minute", var_name="service", value_name="value")
    return (
        alt.Chart(long, height=240)
        .mark_line(strokeWidth=1.4)
        .encode(
            x=alt.X("minute:Q", title="minute"),
            y=alt.Y("value:Q", title=y_label),
            color=alt.Color("service:N", legend=alt.Legend(orient="bottom", title=None, columns=3)),
            tooltip=["minute", "service", alt.Tooltip("value:Q", format=".3f")],
        )
        .configure(background=p["panel"])
        .configure_axis(
            labelColor=p["muted"],
            titleColor=p["muted"],
            gridColor=p["border"],
            domainColor=p["border"],
            tickColor=p["border"],
        )
        .configure_legend(labelColor=p["text"])
        .configure_view(stroke=None)
    )
