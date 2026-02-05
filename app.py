import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime, time, timedelta

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Hardloop Kledingadvies",
    page_icon="🏃‍♂️",
    layout="centered"
)

st.title("🏃‍♂️ Hardloop kledingadvies")

# -------------------------------------------------
# Locatie
# -------------------------------------------------
st.subheader("📍 Locatie")

plaats = st.text_input("Stad / plaats", value="Lelystad")
if not plaats:
    st.stop()

geo_url = (
    "https://geocoding-api.open-meteo.com/v1/search"
    f"?name={plaats}&count=1&language=nl&format=json"
)

geo = requests.get(geo_url, timeout=10).json()
if "results" not in geo:
    st.error("❌ Locatie niet gevonden")
    st.stop()

loc = geo["results"][0]
lat, lon = loc["latitude"], loc["longitude"]

st.caption(f"Gevonden locatie: {loc['name']}, {loc['country']}")

# -------------------------------------------------
# Run instellingen
# -------------------------------------------------
st.subheader("🏃‍♂️ Jouw run")

duur_min = st.slider("Duur van de run (minuten)", 10, 180, 60, step=5)
starttijd = st.time_input("Starttijd", value=time(18, 0))

today = datetime.now().date()
start_dt = datetime.combine(today, starttijd)
eind_dt = start_dt + timedelta(minutes=duur_min)

# -------------------------------------------------
# Weer forecast ophalen (hourly)
# -------------------------------------------------
weather_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,apparent_temperature,precipitation,weathercode"
    "&timezone=auto"
)

hourly = requests.get(weather_url, timeout=10).json()["hourly"]

times = [datetime.fromisoformat(t) for t in hourly["time"]]
now = datetime.now().replace(minute=0, second=0)

rows = []
for i, t in enumerate(times):
    if t.date() == today and t >= now:
        rows.append({
            "tijd": t,
            "uur": t.strftime("%H:%M"),
            "temperatuur": hourly["temperature_2m"][i],
            "gevoel": hourly["apparent_temperature"][i],
            "neerslag": hourly["precipitation"][i],
            "weer_code": hourly["weathercode"][i],
            "looptijd": start_dt <= t <= eind_dt
        })

df = pd.DataFrame(rows)

# -------------------------------------------------
# Weer interpretatie
# -------------------------------------------------
def weer_label(code):
    if code in [0]:
        return "Zonnig ☀️"
    if code in [1, 2]:
        return "Licht bewolkt ⛅"
    if code in [3]:
        return "Bewolkt ☁️"
    if code in [45, 48]:
        return "Mist 🌫️"
    if code in [51, 53, 55, 61, 63, 65]:
        return "Regen 🌧️"
    if code in [71, 73, 75]:
        return "Sneeuw ❄️"
    return "Onbekend"

df["weer"] = df["weer_code"].apply(weer_label)

# -------------------------------------------------
# Score functie
# -------------------------------------------------
def running_score(feels, rain):
    score = 10
    if feels < 0:
        score -= 3
    elif feels < 5:
        score -= 2
    elif feels > 20:
        score -= 2
    if rain > 1:
        score -= 3
    elif rain > 0:
        score -= 1
    return max(1, min(10, score))

df["score"] = df.apply(lambda r: running_score(r["gevoel"], r["neerslag"]), axis=1)

# -------------------------------------------------
# Weer op starttijd
# -------------------------------------------------
closest = df.iloc[(df["tijd"] - start_dt).abs().argsort().iloc[0]]

st.subheader("🌦️ Weer tijdens jouw run")
st.write(f"🌡️ Temperatuur: **{closest['temperatuur']:.1f} °C**")
st.write(f"🥶 Gevoelstemperatuur: **{closest['gevoel']:.1f} °C**")
st.write(f"🌧️ Neerslag: **{closest['neerslag']:.1f} mm/u**")
st.write(f"🌤️ Weer: **{closest['weer']}**")

# -------------------------------------------------
# Grafiek
# -------------------------------------------------
st.subheader("📊 Weersverwachting – rest van vandaag")

base = alt.Chart(df).encode(
    x=alt.X("uur:N", title="Uur")
)

# Achtergrond highlight looptijd
highlight = base.mark_rect(opacity=0.15).encode(
    x="uur:N",
    color=alt.condition(
        alt.datum.looptijd,
        alt.value("#8BC34A"),
        alt.value("transparent")
    )
)

temp_line = base.mark_line(color="red").encode(
    y=alt.Y("temperatuur:Q", title="Temperatuur (°C)"),
    tooltip=["uur", "temperatuur", "gevoel", "neerslag", "weer", "score"]
)

feel_line = base.mark_line(color="blue", strokeDash=[4,2]).encode(
    y="gevoel:Q"
)

rain_bar = base.mark_bar(color="steelblue", opacity=0.4).encode(
    y=alt.Y("neerslag:Q", title="Neerslag (mm)")
)

chart = alt.layer(
    highlight,
    rain_bar,
    temp_line,
    feel_line
).resolve_scale(
    y="independent"
)

st.altair_chart(chart, use_container_width=True)

# -------------------------------------------------
# Tabel (extra duidelijkheid)
# -------------------------------------------------
st.subheader("📋 Overzicht per uur")

st.dataframe(
    df[["uur", "weer", "temperatuur", "gevoel", "neerslag", "score", "looptijd"]],
    hide_index=True
)

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.caption(
    f"📍 {plaats} • 🕒 {start_dt.strftime('%H:%M')}–{eind_dt.strftime('%H:%M')} • "
    f"⏱️ {duur_min} min"
)
