from __future__ import annotations

import csv
from collections import Counter, defaultdict
from html import escape
from math import cos, radians, sin
from pathlib import Path

import streamlit as st


st.set_page_config(page_title="Netflix Insights", page_icon="N", layout="wide")

NETFLIX_RED = "#e50914"
PANEL = "#1f1f1f"
WHITE = "#f5f5f1"
MUTED = "#a7a7a7"
RED_SHADES = ["#e50914", "#b20710", "#f04452", "#7d1017", "#ff737a", "#500b10"]


@st.cache_data
def load_data() -> list[dict[str, str]]:
    csv_path = Path(__file__).with_name("netflix.csv")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        records = list(csv.reader(source))

    if records and len(records[0]) == 1 and "," in records[0][0]:
        records = [
            next(csv.reader([record[0]])) if len(record) == 1 and "," in record[0] else record
            for record in records
        ]

    if len(records) < 2:
        raise ValueError("The Netflix dataset is empty or could not be read.")

    header = records[0]
    return [
        dict(zip(header, record))
        for record in records[1:]
        if len(record) == len(header)
    ]


def aggregate_sum(rows: list[dict[str, str]], group: str, value: str) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        try:
            totals[row[group]] += float(row[value])
        except (KeyError, ValueError):
            continue
    return dict(sorted(totals.items()))


def make_bar_chart(values: dict[str, float], title: str, value_label: str) -> str:
    width, height = 620, 380
    left, right, top, bottom = 62, 22, 62, 82
    plot_width, plot_height = width - left - right, height - top - bottom
    maximum = max(values.values(), default=0) or 1
    bar_width = plot_width / max(len(values), 1) * 0.56
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" '
        'xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">',
        f'<text x="{left}" y="30" fill="{WHITE}" font-size="17" font-weight="700">{escape(title)}</text>',
    ]

    for tick in range(5):
        fraction = tick / 4
        y = top + plot_height * (1 - fraction)
        label = maximum * fraction
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#3b3b3b"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" fill="{MUTED}" font-size="11">{label:,.0f}</text>')

    for index, (label, value) in enumerate(values.items()):
        center = left + plot_width * (index + 0.5) / max(len(values), 1)
        bar_height = plot_height * value / maximum
        y = top + plot_height - bar_height
        parts.append(f'<rect x="{center-bar_width/2:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{NETFLIX_RED}"/>')
        parts.append(f'<text x="{center:.1f}" y="{max(y-8, top+12):.1f}" text-anchor="middle" fill="{WHITE}" font-size="11">{value:,.0f}</text>')
        parts.append(f'<text x="{center:.1f}" y="{height-42}" text-anchor="middle" fill="{WHITE}" font-size="11">{escape(label)}</text>')

    parts.extend([
        f'<text x="{left}" y="{height-12}" fill="{MUTED}" font-size="11">{escape(value_label)}</text>',
        '</svg>',
    ])
    return ''.join(parts)


def make_pie_chart(values: dict[str, float], title: str) -> str:
    width, height = 620, 380
    center_x, center_y, radius = 188, 213, 128
    total = sum(values.values()) or 1
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" '
        'xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">',
        f'<text x="28" y="30" fill="{WHITE}" font-size="17" font-weight="700">{escape(title)}</text>',
    ]
    angle = -90.0
    for index, (label, value) in enumerate(values.items()):
        sweep = value / total * 360
        end_angle = angle + sweep
        start_x = center_x + radius * cos(radians(angle))
        start_y = center_y + radius * sin(radians(angle))
        end_x = center_x + radius * cos(radians(end_angle))
        end_y = center_y + radius * sin(radians(end_angle))
        color = RED_SHADES[index % len(RED_SHADES)]
        if sweep >= 359.999:
            parts.append(f'<circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="{color}"/>')
        else:
            large_arc = 1 if sweep > 180 else 0
            parts.append(
                f'<path d="M {center_x} {center_y} L {start_x:.2f} {start_y:.2f} '
                f'A {radius} {radius} 0 {large_arc} 1 {end_x:.2f} {end_y:.2f} Z" '
                f'fill="{color}" stroke="{PANEL}" stroke-width="2"/>'
            )
        legend_y = 83 + index * 34
        parts.append(f'<rect x="370" y="{legend_y-12}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text x="391" y="{legend_y-2}" fill="{WHITE}" font-size="12">{escape(label)}</text>')
        parts.append(f'<text x="590" y="{legend_y-2}" text-anchor="end" fill="{MUTED}" font-size="12">{value:,.0f}</text>')
        angle = end_angle

    parts.append('</svg>')
    return ''.join(parts)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap');
    :root { color-scheme: dark; }
    .stApp { background: #141414; color: #f5f5f1; font-family: 'DM Sans', sans-serif; }
    [data-testid="stHeader"] { background: rgba(20, 20, 20, 0.96); }
    [data-testid="stMainBlockContainer"] { max-width: 1320px; padding-top: 2rem; }
    .brand { display: flex; align-items: center; gap: 18px; padding: 4px 0 26px; border-bottom: 1px solid #383838; margin-bottom: 25px; }
    .brand-mark { display: grid; place-items: center; width: 48px; height: 58px; background: #e50914; color: white; font: 700 38px 'Oswald', sans-serif; line-height: 1; }
    .brand-kicker { color: #e50914; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; margin: 0 0 3px; }
    .brand h1 { color: #f5f5f1; font: 600 33px 'Oswald', sans-serif; margin: 0; line-height: 1.15; }
    .brand-copy { color: #a7a7a7; font-size: 13px; margin: 5px 0 0; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: #1f1f1f; border-color: #343434; border-radius: 5px; }
    [data-testid="stCaptionContainer"] { color: #a7a7a7; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <header class="brand">
      <div class="brand-mark">N</div>
      <div>
        <p class="brand-kicker">Viewing analytics</p>
        <h1>Netflix data analysis</h1>
        <p class="brand-copy">A focused view of revenue, ratings, and subscription plans</p>
      </div>
    </header>
    """,
    unsafe_allow_html=True,
)

try:
    netflix = load_data()
except (OSError, ValueError) as error:
    st.error(f"Unable to load netflix.csv: {error}")
    st.stop()

required_columns = {"Region", "Monthly_Revenue", "Subscription_Plan", "Rating", "Category"}
available_columns = netflix[0].keys() if netflix else set()
missing_columns = required_columns.difference(available_columns)
if missing_columns:
    st.error(f"The dataset is missing required columns: {', '.join(sorted(missing_columns))}")
    st.stop()

regional_revenue = aggregate_sum(netflix, "Region", "Monthly_Revenue")
plan_ratings = aggregate_sum(netflix, "Subscription_Plan", "Rating")
rating_counts = dict(sorted(Counter(row["Rating"] for row in netflix if row["Rating"]).items()))
category_revenue = aggregate_sum(netflix, "Category", "Monthly_Revenue")

left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown(make_bar_chart(regional_revenue, "Region-wise revenue", "Monthly revenue"), unsafe_allow_html=True)

with right:
    with st.container(border=True):
        st.markdown(make_pie_chart(plan_ratings, "Subscription plan-wise rating"), unsafe_allow_html=True)

left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown(make_bar_chart(rating_counts, "Rating distribution", "Rating count"), unsafe_allow_html=True)

with right:
    with st.container(border=True):
        st.markdown(make_pie_chart(category_revenue, "Category-wise revenue"), unsafe_allow_html=True)