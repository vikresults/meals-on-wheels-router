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

# --- SIDEBAR: CLEAN & COLLAPSIBLE ---
st.sidebar.header("⚙️ Route Setup")

# Use expanders so they don't take up the whole screen
with st.sidebar.expander("📍 Add Start & End Nodes", expanded=False):
    m_addr = st.text_input("Address:")
    if st.button("Set as START"):
        st.session_state.start_node = m_addr
        st.rerun()
    if st.button("Set as END"):
        st.session_state.end_node = m_addr
        st.rerun()

with st.sidebar.expander("🔍 Search & Add Stops", expanded=False):
    q = st.text_input("Search Place:")
    if st.button("Find on Map"):
        res = ArcGIS().geocode(f"{q}, North Carolina")
        if res:
            st.session_state.last_search = res.address
            st.info(f"Found: {res.address}")
    if 'last_search' in st.session_state:
        if st.button("Add Result to List"):
            st.session_state.delivery_list.append(st.session_state.last_search)
            st.rerun()

with st.sidebar.expander("📁 Excel Upload", expanded=False):
    up_file = st.file_uploader("Drop .xlsx here", type=["xlsx"])
    if up_file:
        df = pd.read_excel(up_file)
        if 'Address' in df.columns:
            raw = df['Address'].dropna().astype(str).tolist()
            for a in raw:
                if a.strip() not in st.session_state.delivery_list:
                    st.session_state.delivery_list.append(a.strip())
            st.success("List Updated!")
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




