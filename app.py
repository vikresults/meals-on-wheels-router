import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import ArcGIS
import urllib.parse
from PIL import Image
import pytesseract

# 1. Page Config
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
if 'last_added' not in st.session_state:
    st.session_state.last_added = ""

st.title("🚚 Meals on Wheels: NC Elite Router")

# --- SIDEBAR ---
st.sidebar.header("➕ Add Locations")
tab_man, tab_sea, tab_cam = st.sidebar.tabs(["✍️ Manual/Excel", "🔍 Search", "📸 Camera"])

# TAB 1: MANUAL & EXCEL
with tab_man:
    m_addr = st.text_input("Enter address:")
    c1, c2, c3 = st.columns(3)
    if c1.button("START", key="m1"):
        st.session_state.start_node = m_addr
        st.rerun()
    if c2.button("STOP", key="m2"):
        if m_addr and m_addr not in st.session_state.delivery_list:
            st.session_state.delivery_list.append(m_addr)
            st.session_state.last_added = m_addr
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
            added = 0
            for a in raw:
                if a.strip() and a.strip() not in st.session_state.delivery_list:
                    st.session_state.delivery_list.append(a.strip())
                    added += 1
            st.sidebar.success(f"Added {added} stops!")

# TAB 2: SEARCH
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
        if st.button("Add as STOP", key="s_add"):
            if st.session_state.last_search not in st.session_state.delivery_list:
                st.session_state.delivery_list.append(st.session_state.last_search)
                st.session_state.last_added = st.session_state.last_search
            st.rerun()

# TAB 3: CAMERA (OCR)
with tab_cam:
    cam_img = st.camera_input("Snap an address")
    if cam_img:
        img = Image.open(cam_img)
        try:
            text = pytesseract.image_to_string(img)
            st.write(f"**Read Text:** {text}")
            if st.button("Add to List"):
                st.session_state.delivery_list.append(text.strip())
                st.rerun()
        except:
            st.warning("OCR Engine (Tesseract) not found on PC. Manual entry recommended.")

if st.session_state.last_added:
    st.sidebar.success(f"✅ Added: {st.session_state.last_added[:30]}...")

if st.sidebar.button("🗑️ Reset All", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# --- MAIN UI ---
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📋 Delivery Plan")
    
    # Start Logic
    if st.session_state.start_node:
        st.success(f"🚩 **START:** {st.session_state.start_node}")
    else:
        if st.button("📍 Use My Current Location"):
            st.session_state.start_node = "My Location"
            st.rerun()
    
    # End Logic
    if st.session_state.end_node:
        st.error(f"🏁 **END:** {st.session_state.end_node}")

    st.write("### Checklist")
    # Clean nulls
    st.session_state.delivery_list = [x for x in st.session_state.delivery_list if str(x).lower() != 'nan']
    for i, addr in enumerate(st.session_state.delivery_list):
        done = addr in st.session_state.completed_stops
        if st.checkbox(f"{i+1}. {addr[:60]}", value=done, key=f"ch_{i}"):
            st.session_state.completed_stops.add(addr)
        else:
            st.session_state.completed_stops.discard(addr)

with col_right:
    st.subheader("🗺️ Map & GPS")
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