import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import ArcGIS
import urllib.parse

# 1. Setup
st.set_page_config(page_title="Meals on Wheels Master", layout="wide")

# 2. Memory Initialization
if 'delivery_list' not in st.session_state:
    st.session_state.delivery_list = []
if 'completed_stops' not in st.session_state:
    st.session_state.completed_stops = set()
if 'start_node' not in st.session_state:
    st.session_state.start_node = ""
if 'end_node' not in st.session_state:
    st.session_state.end_node = ""

st.title("🚚 Meals on Wheels: Master Router")

# --- SIDEBAR ---
st.sidebar.header("➕ Add Locations")
tab_man, tab_sea = st.sidebar.tabs(["✍️ Manual/Excel", "🔍 Search"])

with tab_man:
    m_addr = st.text_input("Enter address:")
    c1, c2, c3 = st.columns(3)
    if c1.button("START", key="m1"):
        st.session_state.start_node = m_addr
        st.rerun()
    if c2.button("STOP", key="m2"):
        if m_addr and m_addr not in st.session_state.delivery_list:
            st.session_state.delivery_list.append(m_addr)
        st.rerun()
    if c3.button("END", key="m3"):
        st.session_state.end_node = m_addr
        st.rerun()

    st.divider()
    up_file = st.file_uploader("Upload Excel", type=["xlsx"])
    if up_file:
        df = pd.read_excel(up_file)
        if 'Address' in df.columns:
            raw = df['Address'].dropna().astype(str).tolist()
            for a in raw:
                if a.strip() and a.strip() not in st.session_state.delivery_list:
                    st.session_state.delivery_list.append(a.strip())
            st.sidebar.success("Excel Loaded!")

with tab_sea:
    with st.form("s_form"):
        q = st.text_input("Search NC Map:")
        s_sub = st.form_submit_button("Find")
    if s_sub and q:
        res = ArcGIS().geocode(f"{q}, North Carolina")
        if res:
            st.session_state.last_search = res.address
            st.info(f"Found: {res.address}")
    
    if 'last_search' in st.session_state:
        if st.sidebar.button("Add Search Result as STOP"):
            st.session_state.delivery_list.append(st.session_state.last_search)
            st.rerun()

if st.sidebar.button("🗑️ Reset All Data", use_container_width=True):
    st.session_state.clear()
    st.rerun()

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
