import streamlit as st

st.set_page_config(page_title="Hardloop Kledingadvies", page_icon="🏃‍♂️")

st.title("🏃‍♂️ Hardloop kledingadvies")

temp = st.slider("Temperatuur (°C)", min_value=-10, max_value=25, value=2)
wind = st.checkbox("Winderig")

st.subheader("Advies")

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

if temp <= 3:
    advies.append("🧤 Dunne handschoenen")
    advies.append("🧣 Buff of dunne muts")

if wind:
    advies.append("🧥 Licht winddicht hardloopjack")

for item in advies:
    st.write(item)
