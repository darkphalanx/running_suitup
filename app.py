import streamlit as st
import requests
from datetime import time
import streamlit.components.v1 as components

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
# Session state init
# -------------------------------------------------
for key in ["lat", "lon", "location_received"]:
    if key not in st.session_state:
        st.session_state[key] = None

# -------------------------------------------------
# Browser geolocatie via JS
# -------------------------------------------------
components.html(
    """
    <script>
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const data = {
                lat: position.coords.latitude,
                lon: position.coords.longitude
            };
            window.parent.postMessage(
                { type: "STREAMLIT_LOCATION", payload: data },
                "*"
            );
        },
        function(error) {
            window.parent.postMessage(
                { type: "STREAMLIT_LOCATION_DENIED" },
                "*"
            );
        }
    );
    </script>
    """,
    height=0,
)

# -------------------------------------------------
# Ontvangen van JS events
# -------------------------------------------------
if "_js_event" not in st.session_state:
    st.session_state["_js_event"] = None

event = st.session_state.get("_js_event")

if isinstance(event, dict):
    if event.get("type") == "STREAMLIT_LOCATION":
        st.session_state.lat = event["payload"]["lat"]
        st.session_state.lon = event["payload"]["lon"]
        st.session_state.location_received = True

# -------------------------------------------------
# Locatie check
# -------------------------------------------------
if not st.session_state.location_received:
    st.info("📍 Locatie ophalen via browser… sta dit toe.")
    st.stop()

lat = st.session_state.lat
lon = st.session_state.lon

# -------------------------------------------------
# Weer ophalen (Open-Meteo)
# -------------------------------------------------
weather_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}&longitude={lon}"
    "&current_weather=true"
)

response = requests.get(weather_url, timeout=10)
weather_data = response.json()["current_weather"]

temperature = weather_data["temperature"]
wind_speed = weather_data["windspeed"]

st.subheader("🌦️ Actuele omstandigheden")
st.write(f"🌡️ Temperatuur: **{temperature:.1f} °C**")
st.write(f"💨 Wind: **{wind_speed:.0f} km/u**")

# -------------------------------------------------
# Run instellingen
# -------------------------------------------------
st.subheader("🏃‍♂️ Jouw run")

duration_minutes = st.slider(
    "Duur van de run (minuten)",
    min_value=10,
    max_value=180,
    value=60,
    step=5
)

start_time = st.time_input(
    "Verwachte starttijd",
    value=time(18, 0)
)

# -------------------------------------------------
# Kledingadvies logica
# -------------------------------------------------
st.subheader("👕 Kledingadvies")

advies = []

# Boven- en onderlichaam
if temperature <= 5:
    advies.append("👕 Thermisch ondershirt (lange mouw)")
    advies.append("👖 Lange hardlooptight")
elif temperature <= 12:
    advies.append("👕 Longsleeve")
    advies.append("👖 Lange hardlooptight")
else:
    advies.append("👕 Shirt korte mouw")
    advies.append("🩳 Korte broek")

# Wind / kou accessoires
if temperature <= 3 or wind_speed >= 20:
    advies.append("🧤 Dunne hardloophandschoenen")
    advies.append("🧣 Buff of dunne muts")

# Windjack
if wind_speed >= 15:
    advies.append("🧥 Licht winddicht hardloopjack")

# Langere runs
if duration_minutes >= 90:
    advies.append("🩹 Anti-schuurmaatregelen (bodyglide / tape)")

# -------------------------------------------------
# Output
# -------------------------------------------------
for item in advies:
    st.write(item)

st.caption(
    f"📍 Advies gebaseerd op actuele omstandigheden en een run van "
    f"{duration_minutes} min om {start_time.strftime('%H:%M')}."
)
