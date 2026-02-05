import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Hardloop kledingadvies",
    page_icon="🏃‍♂️",
    layout="centered"
)

# -------------------------------------------------
# THEME-AWARE CSS
# -------------------------------------------------
st.markdown("""
<style>
:root {
    --card-dark: #1e1e1e;
    --card-light: #ffffff;
    --text-dark: #e6e6e6;
    --text-light: #1f1f1f;
    --muted-dark: #aaaaaa;
    --muted-light: #666666;
}

@media (prefers-color-scheme: dark) {
    .card { background: var(--card-dark); color: var(--text-dark); }
    .meta { color: var(--muted-dark); }
}
@media (prefers-color-scheme: light) {
    .card { background: var(--card-light); color: var(--text-light); }
    .meta { color: var(--muted-light); }
}

.card {
    border-radius: 18px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

.hero {
    text-align: center;
    padding: 2.4rem;
}

.score {
    font-size: 72px;
    font-weight: 800;
}

.meta {
    font-size: 0.95rem;
    margin-top: -6px;
}

.section-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

.advice-item {
    padding: 0.7rem 0.9rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.06);
    margin-bottom: 0.6rem;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Helpers: emoji + betekenis
# -------------------------------------------------
def weer_emoji(code, nacht=False):
    if code == 0: return "🌙" if nacht else "☀️"
    if code == 1: return "🌙☁️" if nacht else "🌤️"
    if code == 2: return "☁️🌙" if nacht else "⛅"
    if code == 3: return "☁️"
    if code in [45, 48]: return "🌫️"
    if code in [51, 53]: return "🌦️"
    if code in [55, 61]: return "🌧️"
    if code == 63: return "🌧️🌧️"
    if code == 65: return "🌧️⛈️"
    if code in [71, 73, 75]: return "❄️"
    if code in [80, 81]: return "🌦️🌬️"
    if code in [82, 95]: return "⛈️"
    return "❔"

def weer_betekenis(code):
    mapping = {
        0:"Helder",1:"Overwegend helder",2:"Licht bewolkt",3:"Bewolkt",
        45:"Mist",48:"Mist",
        51:"Motregen",53:"Motregen",55:"Zware motregen",
        61:"Lichte regen",63:"Matige regen",65:"Zware regen",
        71:"Sneeuw",73:"Sneeuw",75:"Sneeuw",
        80:"Regenbuien",81:"Regenbuien",82:"Zware buien",
        95:"Onweer"
    }
    return mappi
