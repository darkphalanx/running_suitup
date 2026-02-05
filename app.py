import streamlit as st
import requests
from datetime import datetime, time, timedelta
import pandas as pd

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
# Weer forecast ophalen
# -------------------------------------------------
weather_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,apparent_temperature,precipitation,wind_speed_10m"
    "&timezone=auto"
)

weather = requests.get(weather_url, timeout=10).json()["hourly"]

times = [datetime.fromisoformat(t) for t in weather["time"]]
temps = weather["temperature_2m"]
feels = weather["apparent_temperature"]
rain = weather["precipitation"]
wind = weather["wind_speed_10m"]

now = datetime.now().replace(minute=0, second=0)

rows = []
for i, t in enumerate(times):
    if t.date() == today and t >= now:
        rows.append({
            "tijd": t,
            "uur": t.strftime("%H:%M"),
            "temperatuur": temps[i],
            "gevoel": feels[i],
            "neerslag": rain[i],
            "wind": wind[i],
            "looptijd": start_dt <= t <= eind_dt
        })

df = pd.DataFrame(rows)

# -------------------------------------------------
# Score functie (1–10)
# -------------------------------------------------
def running_score(feels_like, rain_mm, wind_kmh):
    score = 10

    if feels_like < 0:
        score -= 3
    elif feels_like < 5:
        score -= 2
    elif feels_like > 20:
        score -= 2

    if rain_mm > 1:
        score -= 3
    elif rain_mm > 0:
        score -= 1

    if wind_kmh > 25:
        score -= 2
    elif wind_kmh > 15:
        score -= 1

    return max(1, min(10, score))

df["score"] = df.apply(
    lambda r: running_score(r["gevoel"], r["neerslag"], r["wind"]),
    axis=1
)

# -------------------------------------------------
# Weer op starttijd
# -------------------------------------------------
closest = df.iloc[(df["tijd"] - start_dt).abs().argsort().iloc[0]]

st.subheader("🌦️ Weer tijdens jouw run")
st.write(f"🌡️ Temperatuur: **{closest['temperatuur']:.1f} °C**")
st.write(f"🥶 Gevoelstemperatuur: **{closest['gevoel']:.1f} °C**")
st.write(f"🌧️ Neerslag: **{closest['neerslag']:.1f} mm/u**")
st.write(f"💨 Wind: **{closest['wind']:.0f} km/u**")

# -------------------------------------------------
# Kledingadvies
# -------------------------------------------------
st.subheader("👕 Kledingadvies")

advies = []

if closest["gevoel"] <= 5:
    advies += ["👕 Thermisch ondershirt (lange mouw)", "👖 Lange hardlooptight"]
elif closest["gevoel"] <= 12:
    advies += ["👕 Longsleeve", "👖 Lange hardlooptight"]
else:
    advies += ["👕 Shirt korte mouw", "🩳 Korte broek"]

if closest["gevoel"] <= 3 or closest["wind"] >= 20:
    advies += ["🧤 Dunne handschoenen", "🧣 Buff of dunne muts"]

if closest["wind"] >= 15:
    advies.append("🧥 Licht winddicht hardloopjack")

for a in advies:
    st.write(a)

# -------------------------------------------------
# Grafiek (Streamlit native)
# -------------------------------------------------
st.subheader("📊 Weersverwachting rest van vandaag")

chart_df = df.set_index("uur")[["score"]]
st.line_chart(chart_df)

# Highlight looptijden
st.markdown("**🟩 Gemarkeerde uren = jouw looptijd**")
st.dataframe(
    df[["uur", "score", "looptijd"]],
    hide_index=True
)

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.caption(
    f"📍 {plaats} • 🕒 {start_dt.strftime('%H:%M')}–{eind_dt.strftime('%H:%M')} • "
    f"⏱️ {duur_min} min"
)
