import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import ArcGIS
import urllib.parse

# --- MOBILE FRIENDLY UI STYLING ---
st.set_page_config(page_title="NC Route Master", layout="wide")

st.markdown("""
    <style>
    /* Make buttons big and thumb-friendly */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007BFF;
        color: white;
        font-weight: bold;
        border: none;
        margin-bottom: 10px;
    }
    /* Style the checklist items */
    .stCheckbox {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin-bottom: 8px;
    }
    /* Main container padding for mobile */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Set sidebar width */
    section[data-testid="stSidebar"] {
        width: 425px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚚 NC Elite Router")
# --- 2. RESTORE MEMORY (The Brain) ---
if 'delivery_list' not in st.session_state:
    st.session_state.delivery_list = []
if 'completed_stops' not in st.session_state:
    st.session_state.completed_stops = set()
if 'start_node' not in st.session_state:
    st.session_state.start_node = ""
if 'end_node' not in st.session_state:
    st.session_state.end_node = ""

# --- 3. PROGRESS DASHBOARD ---
# This makes it look like a real delivery app
stops_total = len(st.session_state.delivery_list)
stops_done = len(st.session_state.completed_stops)
stops_remaining = stops_total - stops_done

col_a, col_b, col_c = st.columns(3)
col_a.metric("Total Stops", stops_total)
col_b.metric("Completed", stops_done)
col_c.metric("Remaining", stops_remaining)

st.divider()

# --- SIDEBAR: DUAL-INPUT UPGRADE ---
st.sidebar.header("⚙️ Route Setup")

# 1. START & END NODES
with st.sidebar.expander("🚩 Set Start & End Points", expanded=False):
    st.write("### Start Point")
    s_tab1, s_tab2 = st.tabs(["✍️ Manual", "🔍 Search"])
    with s_tab1:
        if st.button("📍 Use My Current Location"):
            st.session_state.start_node = "My Location"
            st.rerun()
        m_start = st.text_input("Start Address:", key="m_start")
        if st.button("Set Manual Start"):
            st.session_state.start_node = m_start
            st.rerun()
    with s_tab2:
        s_query = st.text_input("Search Start:", key="s_start")
        if st.button("Find & Set Start"):
            res = ArcGIS().geocode(f"{s_query}, North Carolina")
            if res:
                st.session_state.start_node = res.address
                st.success(f"Set: {res.address}")

    st.divider()
    st.write("### End Point")
    e_tab1, e_tab2 = st.tabs(["✍️ Manual", "🔍 Search"])
    with e_tab1:
        m_end = st.text_input("End Address:", key="m_end")
        if st.button("Set Manual End"):
            st.session_state.end_node = m_end
            st.rerun()
    with e_tab2:
        e_query = st.text_input("Search End:", key="e_end")
        if st.button("Find & Set End"):
            res = ArcGIS().geocode(f"{e_query}, North Carolina")
            if res:
                st.session_state.end_node = res.address
                st.success(f"Set: {res.address}")

# 2. DELIVERY STOPS
with st.sidebar.expander("📦 Add Delivery Stops", expanded=True):
    d_tab1, d_tab2, d_tab3 = st.tabs(["✍️ Manual", "🔍 Search", "📁 Excel"])
    with d_tab1:
        m_stop = st.text_input("Enter Stop Address:", key="m_stop")
        if st.button("➕ Add Manual Stop"):
            if m_stop:
                st.session_state.delivery_list.append(m_stop)
                st.rerun()
    with d_tab2:
        d_query = st.text_input("Search Stop:", key="s_stop")
        if st.button("🔍 Find & Add Stop"):
            res = ArcGIS().geocode(f"{d_query}, North Carolina")
            if res:
                st.session_state.delivery_list.append(res.address)
                st.success(f"Added: {res.address}")
    with d_tab3:
        up_file = st.file_uploader("Upload Excel", type=["xlsx"])
        if up_file:
            df = pd.read_excel(up_file)
            if 'Address' in df.columns:
                raw = df['Address'].dropna().astype(str).tolist()
                for a in raw:
                    if a.strip() not in st.session_state.delivery_list:
                        st.session_state.delivery_list.append(a.strip())
                st.success("Excel Stops Added!")

if st.sidebar.button("🗑️ Reset All Data", use_container_width=True):
    st.session_state.clear()
    st.rerun()
# --- 4. MAIN ACTION AREA ---
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📋 Delivery Checklist")
    
    # Filter out empty entries
    st.session_state.delivery_list = [x for x in st.session_state.delivery_list if str(x).lower() != 'nan' and x]
    
    if not st.session_state.delivery_list and not st.session_state.start_node:
        st.info("👋 Welcome! Use the sidebar to add your first delivery address.")
    
    # Display the checklist as clean cards
    for i, addr in enumerate(st.session_state.delivery_list):
        is_done = addr in st.session_state.completed_stops
        # The key ensures Streamlit tracks each checkbox individually
        if st.checkbox(f"{addr}", value=is_done, key=f"addr_{i}"):
            st.session_state.completed_stops.add(addr)
        else:
            st.session_state.completed_stops.discard(addr)

with col_right:
    st.subheader("🗺️ Route Map")
    
    # BIG GOOGLE MAPS BUTTON
    if st.session_state.start_node and st.session_state.delivery_list:
        # Prepare the URL for Google Maps multi-stop
        base_url = "https://www.google.com/maps/dir/"
        start_pt = "Current+Location" if st.session_state.start_node == "My Location" else urllib.parse.quote(st.session_state.start_node)
        
        # Only route the stops NOT yet completed
        remaining_stops = [urllib.parse.quote(str(a)) for a in st.session_state.delivery_list if a not in st.session_state.completed_stops]
        
        dest_pt = ""
        if st.session_state.end_node:
            dest_pt = urllib.parse.quote(st.session_state.end_node)
        elif remaining_stops:
            dest_pt = remaining_stops.pop() # Use the last stop as destination
            
        full_url = f"{base_url}{start_pt}/{'/'.join(remaining_stops)}/{dest_pt}"
        
        st.link_button("🚀 START GPS NAVIGATION", full_url, type="primary", use_container_width=True)
    
    # Visual Map Preview
    m = folium.Map(location=[35.73, -78.85], zoom_start=10, control_scale=True)
    # (Optional: In the future, we can add markers here)
    st_folium(m, width="100%", height=400, returned_objects=[])

if st.button("✨ Optimize My Remaining Route", use_container_width=True):
    # Simple sort for now; keeps the UX snappy
    st.session_state.delivery_list.sort()
    st.rerun()




