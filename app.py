import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import ArcGIS
from geopy.distance import geodesic
import random

# --- 1. CONFIG & STYLING ---
# Note: st.set_page_config MUST be the very first Streamlit command
st.set_page_config(page_title="Universal Router", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
    .stButton > button {
        width: 100%; border-radius: 30px; height: 55px;
        background-color: #000000; color: white; border: none;
        font-size: 18px; font-weight: bold; transition: 0.3s;
    }
    .stButton > button:hover { background-color: #276EF1; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def search_address(query):
    if not query or len(query) < 3:
        return None
    try:
        geolocator = ArcGIS(user_agent="universal_router_v2")
        return geolocator.geocode(query)
    except Exception:
        return None

def get_green_impact(miles_saved):
    kg_co2 = miles_saved * 0.404
    if kg_co2 > 10:
        reward = "🚀 You saved enough CO2 to binge-watch 3 seasons of a show in 4K!"
    elif kg_co2 > 5:
        reward = "☕ That's equivalent to making 150 cups of coffee guilt-free!"
    else:
        reward = "📱 You saved enough energy to charge your phone for a whole year!"
    return kg_co2, reward

# --- 3. NAVIGATION ---
app_phase = st.radio(
    "Select Mode",
    ["📍 Plan Trip", "🚗 Active Drive", "📊 Impact Report"],
    horizontal=True
)
st.divider()

# --- 4. APP PHASES ---

# PHASE 1: PLANNING
if app_phase == "📍 Plan Trip":
    st.info("Search for a destination to see your Green Savings.")
    col1, col2 = st.columns(2)
    
    with col1:
        start_q = st.text_input("Start Location", placeholder="e.g. London, UK", key="start")
    with col2:
        end_q = st.text_input("Destination", placeholder="e.g. Paris, France", key="end")

    if st.button("🗺️ Generate Global Route"):
        if start_q and end_q:
            with st.spinner("Searching global databases..."):
                start_res = search_address(start_q)
                end_res = search_address(end_q)
            
            if start_res and end_res:
                st.session_state.start_node = start_res.address
                st.session_state.end_node = end_res.address
                
                start_coords = (start_res.latitude, start_res.longitude)
                end_coords = (end_res.latitude, end_res.longitude)
                dist = geodesic(start_coords, end_coords).miles
                st.session_state.current_miles = dist
                
                st.balloons()
                st.success(f"Route Found: {dist:.1f} miles")
                
                # Map logic
                avg_lat = (start_res.latitude + end_res.latitude) / 2
                avg_lon = (start_res.longitude + end_res.longitude) / 2
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=4)
                folium.Marker(start_coords, popup="Start", icon=folium.Icon(color='blue')).add_to(m)
                folium.Marker(end_coords, popup="End", icon=folium.Icon(color='green')).add_to(m)
                st_folium(m, width="100%", height=450)
                
                kg, reward = get_green_impact(dist)
                st.info(reward)
            else:
                st.error("📍 Location Not Found. Try adding a city/country name.")
        else:
            st.warning("Please enter both locations.")

# PHASE 2: ACTIVE DRIVE
elif app_phase == "🚗 Active Drive":
    st.subheader("Navigation Center")
    if 'start_node' in st.session_state:
        st.write(f"**From:** {st.session_state.start_node}")
        st.write(f"**To:** {st.session_state.end_node}")
        
        # Proper Google Maps URL
        encoded_start = st.session_state.start_node.replace(" ", "+")
        encoded_end = st.session_state.end_node.replace(" ", "+")
        google_url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_start}&destination={encoded_end}"
        st.link_button("🚀 OPEN GPS NAVIGATION", google_url, type="primary")
    else:
        st.warning("Please plan a trip first!")

# PHASE 3: IMPACT REPORT
elif app_phase == "📊 Impact Report":
    st.subheader("Your Green Scorecard")
    if 'current_miles' in st.session_state:
        kg_saved, reward = get_green_impact(st.session_state.current_miles)
        st.metric("CO2 Avoided", f"{kg_saved:.2f} kg")
        st.info(reward)
        st.success("You are in the top 5% of sustainable drivers this week! 🏆")
    else:
        st.write("No data available yet. Start driving to save carbon!")

st.caption("Global Logistics | Sustainable Routing | 2025")
