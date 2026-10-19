import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas as pd

# Konfiguracja strony
st.set_page_config(
    page_title="Kalkulator Dojazdu - Badania Snu",
    page_icon="🌙",
    layout="centered"
)

# Inicjalizacja geokodera (OpenStreetMap / Nominatim)
@st.cache_resource
def get_geolocator():
    return Nominatim(user_agent="sleep_study_calculator_poland")

geolocator = get_geolocator()

# Baza danych miast techników
TECHNICIAN_HUBS = {
    "Warszawa": (52.2297, 21.0122),
    "Wołomin": (52.3482, 21.2413),
    "Mińsk Mazowiecki": (52.1793, 21.5724)
}

st.title("🌙 Kalkulator Dojazdu na Badanie Snu")
st.markdown("Wpisz miejscowość zamieszkania pacjenta, aby automatycznie obliczyć odległość od najbliższego technika i ustalić cenę końcową.")

# Sekcja wprowadzania danych
st.subheader("1. Miejscowość pacjenta")
city_input = st.text_input("Nazwa miejscowości / Adres:", placeholder="np. Radzymin, Góra Kalwaria, Wyszków...")

if city_input:
    with st.spinner("Szukanie miejscowości i obliczanie odległości..."):
        try:
            # Wyszukiwanie miejscowości w Polsce
            location = geolocator.geocode(f"{city_input}, Polska", timeout=10)
            
            if not location:
                st.error("Nie znaleziono podanej miejscowości. Sprawdź pisownię i spróbuj ponownie.")
            else:
                patient_coords = (location.latitude, location.longitude)
                
                # Obliczanie odległości od każdego z techników
                distances = {}
                for hub_name, hub_coords in TECHNICIAN_HUBS.items():
                    # Odległość geodezyjna * przelicznik trasowy (~1.25 na zakręty i drogi)
                    direct_dist = geodesic(patient_coords, hub_coords).km
                    road_dist = round(direct_dist * 1.25, 1)
                    distances[hub_name] = road_dist
                
                # Znalezienie najbliższego technika
                nearest_hub = min(distances, key=distances.get)
                min_distance = distances[nearest_hub]
                
                # Logika cennika
                BASE_PRICE = 1500
                
                # Sprawdzenie, czy miasto pacjenta to miasto technika
                is_hub_city = any(hub.lower() in city_input.lower() for hub in TECHNICIAN_HUBS.keys())
                
                if is_hub_city or min_distance == 0:
                    zone = "Strefa 0 (Miasto Technika)"
                    travel_fee = 0
                    min_distance = 0
                elif min_distance <= 29.9:
                    zone = "Strefa 1 (do 29 km)"
                    travel_fee = 100
                elif min_distance <= 50.0:
                    zone = "Strefa 2 (30 - 50 km)"
                    travel_fee = 200
                else:
                    zone = "Poza obszarem dojazdu"
                    travel_fee = None

                # Wyniki
                st.divider()
                st.subheader("2. Wynik wyceny")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Znaleziona miejscowość", location.address.split(",")[0])
                    st.metric("Najbliższa baza technika", nearest_hub)
                with col2:
                    st.metric("Szacowana odległość", f"{min_distance} km")
                    st.metric("Przypisana strefa", zone)
                
                st.divider()
                
                # Podsumowanie kosztów
                if travel_fee is not None:
                    total_cost = BASE_PRICE + travel_fee
                    st.success(f"### 💰 Razem do zapłaty: {total_cost} PLN")
                    st.write(f"- Cena badania polisomnograficznego: **{BASE_PRICE} PLN**")
                    st.write(f"- Dopłata za dojazd ({zone}): **{travel_fee} PLN**")
                else:
                    st.error("⚠️ **Uwaga:** Miejscowość znajduje się powyżej 50 km od najbliższej bazy technika. Brak możliwości dojazdu w trybie standardowym.")

        except Exception as e:
            st.error(f"Wystąpił błąd podczas połączenia z bazą map: {e}")

# Boczny panel zarządzania
with st.sidebar:
    st.header("⚙️ Bazy Techników")
    st.write("Obecne lokalizacje techników:")
    for hub in TECHNICIAN_HUBS.keys():
        st.write(f"- **{hub}**")
    
    st.divider()
    st.header("💵 Cennik stref")
    st.write("- **Strefa 0:** 0 PLN (Warszawa i miasta techników)")
    st.write("- **Strefa 1 (0-29 km):** +100 PLN")
    st.write("- **Strefa 2 (30-50 km):** +200 PLN")
    st.write("- **Powyżej 50 km:** Brak możliwości")