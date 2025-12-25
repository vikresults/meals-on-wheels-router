import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import ArcGIS
from geopy.distance import geodesic
import random

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Universal Router", layout="wide")

# --- 2. STYLING (Uber/Black Theme) ---
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

# --- 3. HELPER FUNCTIONS ---
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

# --- 4. NAVIGATION BAR ---
st.title("🌐 Universal Router")
app_phase = st.radio(
    "Select Mode",
    ["📍 Plan Trip", "🚗 Active Drive", "📊 Impact Report"],
    horizontal=True
)
st.divider()

# --- 5. PHASE LOGIC ---

# PHASE 1: PLANNING
if app_phase == "📍 Plan Trip":
    st.info("Search for a destination to see your Green Savings.")
    
    # Grid for inputs
    col1, col2 = st.columns(2)
    with col1:
        start_q = st.text_input("Start Location", placeholder="e.g. London, UK", key="start_input")
    with col2:
        end_q = st.text_input("Destination", placeholder="e.g. Paris, France", key="end_input")

    if st.button("🗺️ Generate Global Route"):
        if start_q and end_q:
            with st.spinner("Calculating route..."):
                start_res = search_address(start_q)
                end_res = search_address(end_q)
            
            if start_res and end_res:
                # Save to session memory
                st.session_state.start_node = start_res.address
                st.session_state.end_node = end_res.address
                
                # Math
                start_coords = (start_res.latitude, start_res.longitude)
                end_coords = (end_res.latitude, end_res.longitude)
                dist = geodesic(start_coords, end_coords).miles
                st.session_state.current_miles = dist
                
                # Display Results
                st.balloons()
                st.success(f"Route Found: {dist:.1f} miles")
                
                # Map Generation
                avg_lat = (start_res.latitude + end_res.latitude) / 2
                avg_lon = (start_res.longitude + end_res.longitude) / 2
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=4)
                folium.Marker(start_coords, popup="Start", icon=folium.Icon(color='blue')).add_to(m)
                folium.Marker(end_coords, popup="End", icon=folium.Icon(color='green')).add_to(m)
                st_folium(m, width="100%", height=450)
                
                kg, reward = get_green_impact(dist)
                st.info(reward)
            else:
                st.error("📍 Location Not Found. Please try adding a city name.")
        else:
            st.warning("Please fill in both fields.")

# PHASE 2: ACTIVE DRIVE
elif app_phase == "🚗 Active Drive":
    st.subheader("Navigation Center")
    if 'start_node' in st.session_state:
        st.write(f"🚩 **Current Route:** {st.session_state.start_node} → {st.session_state.end_node}")
        
        # Link to external GPS
        encoded_start = st.session_state.start_node.replace(" ", "+")
        encoded_end = st.session_state.end_node.replace(" ", "+")
        google_url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_start}&destination={encoded_end}"
        
        st.link_button("🚀 LAUNCH LIVE GPS", google_url, type="primary")
    else:
        st.warning("Please go to 'Plan Trip' first to set your destination.")

# PHASE 3: IMPACT REPORT
elif app_phase == "📊 Impact Report":
    st.subheader("Your Green Scorecard")
    if 'current_miles' in st.session_state:
        kg_saved, reward = get_green_impact(st.session_state.current_miles)
        
        col_metric, col_reward = st.columns([1, 2])
        with col_metric:
            st.metric("CO2 Avoided", f"{kg_saved:.2f} kg")
        with col_reward:
            st.success(reward)
            
        st.caption("Calculation based on GSF Standards (0.404kg/mile).")
    else:
        st.write("No trip data found. Complete a trip to see your impact!")

st.divider()
st.caption("Universal Router v2.0 | Sustainable Logistics | 2025")
