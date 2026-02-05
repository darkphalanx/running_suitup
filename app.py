import streamlit as st
import requests
from datetime import datetime, time, timedelta
import matplotlib.pyplot as plt

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
    "&hourly=temperature_2m,apparent_temperature,precipitation,wind_speed_10m"
    "&timezone=auto"
)

weather = requests.get(weather_url, timeout=10).json()["hourly"]

times = [datetime.fromisoformat(t) for t in weather["time"]]
temps = weather["temperature_2m"]
feels = weather["apparent_temperature"]
rain = weather["precipitation"]
wind = weather["wind_speed_10m"]

# -------------------------------------------------
# Filter: resterende uren vandaag
# -------------------------------------------------
now = datetime.now()
indices_today = [
    i for i, t in enumerate(times)
    if t.date() == today and t >= now.replace(minute=0, second=0)
]

# -------------------------------------------------
# Score functie (1–10)
# -------------------------------------------------
def running_score(temp, feels_like, rain_mm, wind_kmh):
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

scores = [
    running_score(temps[i], feels[i], rain[i], wind[i])
    for i in indices_today
]

# -------------------------------------------------
# Weer op starttijd
# -------------------------------------------------
closest_idx = min(
    indices_today,
    key=lambda i: abs(times[i] - start_dt)
)

st.subheader("🌦️ Weer tijdens jouw run")

st.write(f"🌡️ Temperatuur: **{temps[closest_idx]:.1f} °C**")
st.write(f"🥶 Gevoelstemperatuur: **{feels[closest_idx]:.1f} °C**")
st.write(f"🌧️ Neerslag: **{rain[closest_idx]:.1f} mm/u**")
st.write(f"💨 Wind: **{wind[closest_idx]:.0f} km/u**")

# -------------------------------------------------
# Kledingadvies
# -------------------------------------------------
st.subheader("👕 Kledingadvies")

advies = []

if feels[closest_idx] <= 5:
    advies += ["👕 Thermisch ondershirt (lange mouw)", "👖 Lange hardlooptight"]
elif feels[closest_idx] <= 12:
    advies += ["👕 Longsleeve", "👖 Lange hardlooptight"]
else:
    advies += ["👕 Shirt korte mouw", "🩳 Korte broek"]

if feels[closest_idx] <= 3 or wind[closest_idx] >= 20:
    advies += ["🧤 Dunne handschoenen", "🧣 Buff of dunne muts"]

if wind[closest_idx] >= 15:
    advies.append("🧥 Licht winddicht hardloopjack")

for a in advies:
    st.write(a)

# -------------------------------------------------
# Grafiek
# -------------------------------------------------
st.subheader("📊 Weersverwachting rest van vandaag")

hours = [times[i].hour for i in indices_today]

fig, ax1 = plt.subplots()

ax1.plot(hours, scores)
ax1.set_ylim(0, 10)
ax1.set_ylabel("Loop-score (1–10)")
ax1.set_xlabel("Uur")

# Highlight loop-uren
for i, idx in enumerate(indices_today):
    if start_dt <= times[idx] <= eind_dt:
        ax1.axvspan(hours[i] - 0.5, hours[i] + 0.5)

st.pyplot(fig)

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.caption(
    f"📍 {plaats} • 🕒 {start_dt.strftime('%H:%M')}–{eind_dt.strftime('%H:%M')} • "
    f"⏱️ {duur_min} min"
)
