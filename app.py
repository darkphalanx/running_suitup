import streamlit as st
import requests
from datetime import datetime, time
import streamlit.components.v1 as components

st.set_page_config(page_title="Hardloop Kledingadvies", page_icon="🏃‍♂️")
st.title("🏃‍♂️ Hardloop kledingadvies")

# -------------------------
# Browser geolocatie ophalen
# -------------------------
components.html(
    """
    <script>
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            window.parent.postMessage(
                {lat: lat, lon: lon},
                "*"
            );
        }
    );
    </script>
    """,
    height=0,
)

location = st.experimental_get_query_params()

if "lat" not in st.session_state:
    st.session_state.lat = None
    st.session_state.lon = None

if st.session_state.lat is None:
    st.info("📍 Locatie ophalen via browser… sta dit toe.")
    st.stop()

lat = st.session_state.lat
lon = st.session_state.lon

# -------------------------
# Weer ophalen (Open-Meteo)
# -------------------------
url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}&longitude={lon}"
    "&current_weather=true"
)
weather = requests.get(url).json()["current_weather"]

temp = weather["temperature"]
wind = weather["windspeed"]
weathercode = weather["weathercode"]

st.subheader("🌦️ Actuele omstandigheden")
st.write(f"🌡️ Temperatuur: **{temp} °C**")
st.write(f"💨 Wind: **{wind} km/u**")

# -------------------------
# Run instellingen
# -------------------------
st.subheader("🏃‍♂️ Jouw run")

duur = st.slider("Duur van de run (minuten)", 10, 180, 60)
starttijd = st.time_input("Starttijd", value=time(18, 0))

# -------------------------
# Kledingadvies logica
# -------------------------
st.subheader("👕 Kledingadvies")

advies = []

if temp <= 5:
    advies.append("👕 Thermisch ondershirt (lange mouw)")
    advies.append("👖 Lange hardlooptight")
elif temp <= 12:
    advies.append("👕 Longsleeve")
    advies.append("👖 Lange hardlooptight")
else:
    advies.append("👕 Shirt korte mouw")
    advies.append("🩳 Korte broek")

if temp <= 3 or wind >= 20:
    advies.append("🧤 Dunne handschoenen")
    advies.append("🧣 Buff of dunne muts")

if wind >= 15:
    advies.append("🧥 Licht winddicht hardloopjack")

if duur >= 90:
    advies.append("🧦 Comfortabele sokken (anti-schuur)")

for item in advies:
    st.write(item)
