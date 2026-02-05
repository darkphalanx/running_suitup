import streamlit as st
import requests
from datetime import time

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
# Locatie invoer
# -------------------------------------------------
st.subheader("📍 Locatie")

plaats = st.text_input(
    "Voer je stad of plaats in",
    value="Lelystad"
)

if not plaats:
    st.stop()

# -------------------------------------------------
# Geocoding (Open-Meteo)
# -------------------------------------------------
geo_url = (
    "https://geocoding-api.open-meteo.com/v1/search"
    f"?name={plaats}&count=1&language=nl&format=json"
)

geo_response = requests.get(geo_url, timeout=10).json()

if "results" not in geo_response:
    st.error("❌ Plaats niet gevonden")
    st.stop()

location = geo_response["results"][0]
lat = location["latitude"]
lon = location["longitude"]

st.caption(f"Gevonden locatie: {location['name']}, {location['country']}")

# -------------------------------------------------
# Weer ophalen
# -------------------------------------------------
weather_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}&longitude={lon}"
    "&current_weather=true"
)

weather = requests.get(weather_url, timeout=10).json()["current_weather"]

temperature = weather["temperature"]
wind_speed = weather["windspeed"]

st.subheader("🌦️ Actuele omstandigheden")
st.write(f"🌡️ Temperatuur: **{temperature:.1f} °C**")
st.write(f"💨 Wind: **{wind_speed:.0f} km/u**")

# -------------------------------------------------
# Run instellingen
# -------------------------------------------------
st.subheader("🏃‍♂️ Jouw run")

duration_minutes = st.slider(
    "Duur van de run (minuten)",
    10, 180, 60, step=5
)

start_time = st.time_input(
    "Verwachte starttijd",
    value=time(18, 0)
)

# -------------------------------------------------
# Kledingadvies
# -------------------------------------------------
st.subheader("👕 Kledingadvies")

advies = []

if temperature <= 5:
    advies += [
        "👕 Thermisch ondershirt (lange mouw)",
        "👖 Lange hardlooptight"
    ]
elif temperature <= 12:
    advies += [
        "👕 Longsleeve",
        "👖 Lange hardlooptight"
    ]
else:
    advies += [
        "👕 Shirt korte mouw",
        "🩳 Korte broek"
    ]

if temperature <= 3 or wind_speed >= 20:
    advies += [
        "🧤 Dunne hardloophandschoenen",
        "🧣 Buff of dunne muts"
    ]

if wind_speed >= 15:
    advies.append("🧥 Licht winddicht hardloopjack")

if duration_minutes >= 90:
    advies.append("🩹 Anti-schuurmaatregelen")

for item in advies:
    st.write(item)

st.caption(
    f"📍 {plaats} • 🕒 {start_time.strftime('%H:%M')} • ⏱️ {duration_minutes} min"
)
