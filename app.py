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
# --- MAIN UI ---
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📋 Delivery Plan")
    if st.session_state.start_node:
        st.success(f"🚩 **START:** {st.session_state.start_node}")
    else:
        if st.button("📍 Use My Current Location"):
            st.session_state.start_node = "My Location"
            st.rerun()
    
    if st.session_state.end_node:
        st.error(f"🏁 **END:** {st.session_state.end_node}")

    st.write("### Checklist")
    st.session_state.delivery_list = [x for x in st.session_state.delivery_list if str(x).lower() != 'nan']
    for i, addr in enumerate(st.session_state.delivery_list):
        done = addr in st.session_state.completed_stops
        if st.checkbox(f"{i+1}. {addr}", value=done, key=f"ch_{i}"):
            st.session_state.completed_stops.add(addr)
        else:
            st.session_state.completed_stops.discard(addr)

with col_right:
    st.subheader("🗺️ Map Preview")
    if st.button("✨ Optimize Order", use_container_width=True):
        st.session_state.delivery_list = sorted(list(set(st.session_state.delivery_list)))
        st.rerun()

    if st.session_state.start_node and st.session_state.end_node:
        s_val = "Current+Location" if st.session_state.start_node == "My Location" else st.session_state.start_node
        pts = [s_val] + st.session_state.delivery_list + [st.session_state.end_node]
        url = "https://www.google.com/maps/dir/" + "/".join([urllib.parse.quote(str(p)) for p in pts])
        st.link_button("🚀 Launch GPS Navigation", url, use_container_width=True)

    m = folium.Map(location=[35.73, -78.85], zoom_start=11)
    st_folium(m, width=600, height=400)



