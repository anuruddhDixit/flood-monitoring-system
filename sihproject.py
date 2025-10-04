# build7.py
# Full FloodSafe application (merged updates):
# - Preserves original logic: weather API, folium maps, analytics, shelters, translation, alerts, SOS, etc.
# - UI updates: no hover color, default yellow action buttons, red SOS, sidebar gradient + icons, sidebar headings/subheadings white,
#   sidebar links use smooth scroll anchors, removed duplicate "Emergency Features" section from main content.
#
# Run: streamlit run build7.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import requests
from PIL import Image
import io
import base64
import time
import folium
from streamlit_folium import st_folium
import zipfile
import os

# Optional imports
try:
    from googletrans import Translator
    TRANSLATOR = Translator()
    GT_AVAILABLE = True
except Exception:
    TRANSLATOR = None
    GT_AVAILABLE = False

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(
    page_title="Disaster Alert System",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- YOUR OPENWEATHER API KEY (replace with yours if needed) ---
OPENWEATHER_KEY = "d0c51699c6fdb0f61cf6e05f2d4247fa"

# ----------------------------
# CSS Styling + Smooth Scroll JS
# ----------------------------
# Updated styles:
# - Remove hover color globally
# - Default buttons: yellow
# - SOS: red gradient
# - Sidebar links: gradient + icons, no underline, lift on hover
# - Sidebar headings and subheadings: white
st.markdown("""
<style>
/* App background */
[data-testid="stAppViewContainer"] { background-color: #f0f2f5; color: #111; }

/* Sidebar background and text */
[data-testid="stSidebar"] { 
    background-color: #202124; 
    color: #ffffff; 
    padding-top: 8px;
}

/* Make sidebar headings & subheadings white */
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] label p {
    color: #000000 !important;
}

[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3, 
[data-testid="stSidebar"] .css-1d391kg { color: #ffffff !important; }

/* Form control text in sidebar */
[data-testid="stSidebar"] label, [data-testid="stSidebar"] .stTextInput, [data-testid="stSidebar"] .stNumberInput {
    color: #ffffff !important;
}

/* Remove hover color from all buttons (global) */
.stButton>button, button, [role="button"] {
    transition: none !important;
    -webkit-transition: none !important;
    box-shadow: none !important;
}
.stButton>button:hover, button:hover, [role="button"]:hover {
    background-color: inherit !important;
    color: inherit !important;
    filter: none !important;
}

/* Remove focus glow for buttons */
.stButton>button:focus, button:focus, [role="button"]:focus {
    outline: none !important;
    box-shadow: none !important;
}

/* Default action buttons = Yellow */
.stButton>button, button {
    background-color: #FFD60A !important; /* bright yellow */
    color: #111 !important;
    border: none !important;
    font-weight: 600 !important;
}

/* Generic card styles */
.card { background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.08); margin-bottom: 16px; color:#111; }
.stat-card { background-color: white; border-radius: 10px; padding: 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.06); text-align:center; }
.alert-banner { padding: 12px; border-radius: 8px; margin-bottom: 12px; color: #111; }
.alert-danger { background: #f8d7da; border-left: 6px solid #ea4335; }
.alert-warning { background: #fff3cd; border-left: 6px solid #fbbc05; }
.alert-safe { background: #d4edda; border-left: 6px solid #34a853; }
.feature-card { background: #fff; border-radius: 8px; padding: 12px; text-align:center; box-shadow: 0 3px 8px rgba(0,0,0,0.06); height: 170px; }

/* Sidebar button (gradient with icons) */
.sidebar-btn {
    display:flex;
    align-items:center;
    gap:10px;
    padding:12px 14px;
    margin:8px 0;
    border-radius:10px;
    text-decoration:none !important;   /* remove underline */
    font-weight:600;
    background: linear-gradient(135deg, #42a5f5, #1e88e5);  /* blue gradient */
    color:#fff !important;
    box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
/* lift effect on hover (no color change) */
.sidebar-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.22);
}

/* SOS (red gradient variant) */
.sidebar-btn.sos-link {
    background: linear-gradient(135deg, #e53935, #b71c1c) !important;
    color:white !important;
}
.sidebar-btn.sos-link:hover {
    transform: scale(1.03);
    box-shadow: 0 10px 26px rgba(234,67,53,0.35);
}

/* Floating SOS button (red gradient) */
.sos-button { 
    position: fixed; 
    bottom: 24px; 
    right: 24px; 
    z-index: 9999; 
    width:72px; 
    height:72px; 
    border-radius:50%; 
    background: linear-gradient(135deg, #e53935, #b71c1c) !important;
    color:white !important; 
    display:flex; 
    align-items:center; 
    justify-content:center; 
    font-weight:bold; 
    font-size:18px; 
    box-shadow: 0 6px 18px rgba(234,67,53,0.35);
    transition: all 0.3s ease;
    cursor: pointer;
}
.sos-button:hover {  
    transform: scale(1.08);
    box-shadow: 0 12px 32px rgba(234,67,53,0.45);
}

/* Anchor padding fix so headings aren't hidden under sticky navs */
.section-anchor {
    padding-top: 70px;
    margin-top: -70px;
}

/* small responsive tweaks for folium map container */
.folium-container { width: 100% !important; height: 500px; }


            
</style>

<script>
document.addEventListener("DOMContentLoaded", function() {
    // Delegated click listener for sidebar links with class 'sidebar-btn'
    document.body.addEventListener('click', function(e) {
        const el = e.target;
        // allow clicks on child elements (emoji/text inside <a>)
        const link = el.closest && el.closest('.sidebar-btn') ? el.closest('.sidebar-btn') : (el.classList && el.classList.contains('sidebar-btn') ? el : null);
        if (link) {
            e.preventDefault();
            const href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    history.replaceState(null, null, href);
                }
            }
        }
    }, false);
});
</script>
""", unsafe_allow_html=True)

# ----------------------------
# TRANSLATIONS (small internal dictionary)
# ----------------------------
UI_TEXT = {
    "title": {"en":"Disaster Alert", "hi":"फ़्लडसेफ डैशबोर्ड", "bn":"ফ্লাডসেফ ড্যাশবোর্ড", "ta":"ப்ளட்ஸேஃப் டாஷ்போர்டு"},
    "subtitle": {"en":"Real-time Disaster monitoring and management system", "hi":"रीयल-टाइम बाढ़ निगरानी और प्रबंधन प्रणाली", "bn":"রিয়েল-টাইম বন্যা পর্যবেক্ষণ ও ব্যবস্থাপনা সিস্টেম", "ta":"நேரடி வெள்ள கண்காணிப்பு மற்றும் நிர்வாகம்"},
    "get_location": {"en":"📍 Use My Location", "hi":"📍 मेरा स्थान उपयोग करें", "bn":"📍 আমার অবস্থান ব্যবহার করুন", "ta":"📍 என் இடத்தைப் பயன்படுத்தவும்"},
    "enter_city": {"en":"Or enter city name", "hi":"या शहर का नाम डालें", "bn":"অথবা শহরের নাম লিখুন", "ta":"அல்லது நகரின் பெயரை உள்ளிடவும்"},
    "area_summary": {"en":"Area Summary", "hi":"क्षेत्र सारांश", "bn":"এলাকার সারসংক্ষেপ", "ta":"பகுதி சுருக்கம்"},
    "flood_monitoring_map": {"en":"Flood Monitoring Map", "hi":"बाढ़ निगरानी मानचित्र", "bn":"বন্যা পর্যবেক্ষণ মানচিত্র", "ta":"வெள்ள கண்காணிப்பு வரைபடம்"},
    "download_offline_map": {"en":"⬇ Download Offline Map", "hi":"⬇ ऑफ़लाइन मैप डाउनलोड करें", "bn":"⬇ অফলাইন মানচিত্র ডাউনলোড করুন", "ta":"⬇ ஆஃப்லைன் வரைபடம் பதிவிறக்குக"},
    "sos": {"en":"🚨 SOS Emergency", "hi":"🚨 एसओएस आपातकाल", "bn":"🚨 এসওএস জরুরী", "ta":"🚨 SOS அவசர"},
    "alerts": {"en":"⚠️ View Alerts", "hi":"⚠️ अलर्ट देखें", "bn":"⚠️ alerts দেখুন", "ta":"⚠️ எச்சரிக்கைகளைக் காண்க"},
    "shelters": {"en":"🏠 Find Shelters", "hi":"🏠 आश्रय स्थल खोजें", "bn":"🏠 আশ্রয় খুঁজুন", "ta":"🏠 தங்குமிடங்களைக் கண்டறியவும்"},
    "emergency_contacts": {"en":"📞 Emergency Contacts", "hi":"📞 आपातकालीन संपर्क", "bn":"📞 জরুরী যোগাযোগ", "ta":"📞 அவசர தொடர்புகள்"},
    "safe_zone_locator": {"en":"📌 Safe Zone Locator", "hi":"📌 सुरक्षित क्षेत्र लोकेटर", "bn":"📌 নিরাপদ অঞ্চল লোকেটর", "ta":"📌 பாதுகாப்பான மண்டலம் கண்டுபிடிப்பான்"},
    "search_shelters": {"en":"🔍 Search Nearby Shelters", "hi":"🔍 आस-पास के आश्रय स्थल खोजें", "bn":"🔍 কাছাকাছি আশ্রয় অনুসন্ধান করুন", "ta":"🔍 அருகிலுள்ள தங்குமிடங்களைத் தேடுங்கள்"},
    "evacuation_routes": {"en":"🛣️ Evacuation Routes", "hi":"🛣️ निकासी मार्ग", "bn":"🛣️ সরিয়ে নেওয়ার রুট", "ta":"🛣️ வெளியேற்றம் பாதைகள்"}
}
def ui_t(key, lang_code='en'):
    return UI_TEXT.get(key, {}).get(lang_code, UI_TEXT.get(key, {}).get('en', key))

# ----------------------------
# UTIL: translation helper (tries googletrans, else internal)
# ----------------------------
def translate_text(txt, to_code):
    """
    Attempt to translate `txt` to language code `to_code` using googletrans if available.
    If not available, return original text (we rely mainly on UI_TEXT for keys).
    to_code: 'en','hi','bn','ta'
    """
    if to_code == 'en' or txt is None or txt == "":
        return txt
    if GT_AVAILABLE:
        try:
            res = TRANSLATOR.translate(txt, dest=to_code)
            return res.text
        except Exception:
            return txt
    else:
        return txt

# ----------------------------
# SESSION STATE: coords & language
# ----------------------------
if 'coords' not in st.session_state:
    st.session_state['coords'] = None  # {'lat':..., 'lon':...}

if 'lang' not in st.session_state:
    st.session_state['lang'] = 'en'  # 'en','hi','bn','ta'

# ----------------------------
# EMERGENCY FUNCTIONS
# ----------------------------
def send_emergency_sms():
    """Simulate sending emergency SMS"""
    if st.session_state.get('coords'):
        lat = st.session_state['coords']['lat']
        lon = st.session_state['coords']['lon']
        message = f"EMERGENCY! Need assistance at coordinates: {lat:.6f}, {lon:.6f}. Google Maps: https://www.google.com/maps?q={lat},{lon}"
        st.sidebar.success(f"SMS would be sent with location: {lat:.6f}, {lon:.6f}")
        return message
    else:
        st.sidebar.error("Location not available. Please set your location first.")
        return None

def get_nearby_hospitals(lat, lon, radius=5000):
    """Get nearby hospitals (simulated)"""
    hospitals = [
        {"name": "City General Hospital", "distance": "1.2 km", "phone": "+91-XXX-XXXX-XXX"},
        {"name": "Community Medical Center", "distance": "2.5 km", "phone": "+91-XXX-XXXX-XXX"},
        {"name": "Emergency Care Unit", "distance": "3.1 km", "phone": "+91-XXX-XXXX-XXX"}
    ]
    return hospitals

# ----------------------------
# SIDEBAR: Language, Location, Controls (with anchored emergency nav)
# ----------------------------
st.sidebar.markdown(f"<h2 style='color:white'>🌊 FloodSafe</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚨 Emergency Features")

# Sidebar anchor links (smooth scroll). SOS is a red gradient link; others are blue gradient.
st.sidebar.markdown('<a class="sidebar-btn sos-link" href="#sos-section">🚨 SOS Emergency</a>', unsafe_allow_html=True)
st.sidebar.markdown('<a class="sidebar-btn" href="#view-alerts">⚠️ View Alerts</a>', unsafe_allow_html=True)
st.sidebar.markdown('<a class="sidebar-btn" href="#safe-zone-locator">🏠 Find Shelters</a>', unsafe_allow_html=True)
st.sidebar.markdown('<a class="sidebar-btn" href="#emergency-contacts">📞 Emergency Contacts</a>', unsafe_allow_html=True)
st.sidebar.markdown('<a class="sidebar-btn" href="#evacuation-routes">🛣️ Evacuation Routes</a>', unsafe_allow_html=True)

st.sidebar.markdown("---")

# Language selection
lang_choice = st.sidebar.selectbox("Language / भाषा / ভাষা / மொழி", ["English","Hindi","Bengali","Tamil"])
lang_map = {"English":"en","Hindi":"hi","Bengali":"bn","Tamil":"ta"}
st.session_state['lang'] = lang_map[lang_choice]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔎 Location")
# Geolocation via JS component will be provided in main area (more reliable UX). Provide fallback input here.
lat_manual = st.sidebar.number_input("Latitude", format="%.6f", value=28.613939)
lon_manual = st.sidebar.number_input("Longitude", format="%.6f", value=77.209021)
if st.sidebar.button("Use Manual Coordinates"):
    st.session_state['coords'] = {'lat': float(lat_manual), 'lon': float(lon_manual)}
    st.sidebar.success(f"Using coords: {lat_manual:.6f}, {lon_manual:.6f}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Offline Map")
if st.sidebar.button(ui_t("download_offline_map", st.session_state['lang'])):
    coords = st.session_state.get('coords') or {'lat': lat_manual, 'lon': lon_manual}
    lat0, lon0 = coords['lat'], coords['lon']
    m = folium.Map(location=[lat0, lon0], zoom_start=12)
    folium.TileLayer("OpenStreetMap").add_to(m)
    folium.Marker([lat0, lon0], popup="Selected Location").add_to(m)
    shelters = [
        {"name":"Central High School","lat":lat0+0.003,"lon":lon0+0.004},
        {"name":"Community Center","lat":lat0-0.004,"lon":lon0-0.003},
        {"name":"City Hospital","lat":lat0+0.006,"lon":lon0-0.002}
    ]
    for s in shelters:
        folium.Marker([s['lat'], s['lon']], popup=s['name']).add_to(m)
    offline_html = "offline_map.html"
    m.save(offline_html)
    shelters_geo = {"type":"FeatureCollection","features":[]}
    for s in shelters:
        shelters_geo["features"].append({"type":"Feature","properties":{"name":s['name']},"geometry":{"type":"Point","coordinates":[s['lon'], s['lat']]}})
    zip_name = "offline_package.zip"
    with zipfile.ZipFile(zip_name, "w") as zf:
        zf.write(offline_html)
        zf.writestr("shelters.geojson", json.dumps(shelters_geo))
    with open(zip_name, "rb") as f:
        st.sidebar.download_button("Download Offline Package (HTML + GeoJSON)", data=f, file_name=zip_name, mime="application/zip")
    st.sidebar.success("Offline package prepared. Check download button above.")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Controls")
battery_saver = st.sidebar.checkbox("Battery Saver Mode (text only)", value=False)
offline_mode = st.sidebar.checkbox("Offline Mode (use downloaded files)", value=False)

# ----------------------------
# JS Geolocation component (main area) - posts a window.postMessage
# ----------------------------
def geolocation_component(label):
    geoloc_html = f"""
    <div>
      <button id="getLocBtn" style="padding:10px 14px;border-radius:8px;border:none;background:#1a73e8;color:white;font-weight:600;">
        {label}
      </button>
      <div id="status" style="margin-top:8px;color:#111"></div>
    </div>
    <script>
    const btn = document.getElementById('getLocBtn');
    const status = document.getElementById('status');
    btn.addEventListener('click', () => {{
      if (!navigator.geolocation) {{
        status.innerText = 'Geolocation not supported by your browser';
        return;
      }}
      status.innerText = 'Requesting location...';
      navigator.geolocation.getCurrentPosition(success, error, {{enableHighAccuracy:true, timeout:15000}});
    }});
    function success(position) {{
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;
      status.innerText = 'Location: ' + lat.toFixed(6) + ', ' + lon.toFixed(6);
      const payload = {{lat:lat, lon:lon}};
      window.parent.postMessage({{isStreamlitMessage: true, type: 'geoLocation', payload: payload}}, '*');
    }}
    function error(err) {{
      status.innerText = 'Error: ' + (err.message || 'Unable to get location');
    }}
    </script>
    """
    st.components.v1.html(geoloc_html, height=120)

# ----------------------------
# APP HEADER
# ----------------------------
st.title(ui_t("title", st.session_state['lang']))
st.markdown(f"_{ui_t('subtitle', st.session_state['lang'])}_")

# Show geolocation button in main area for better UX
st.markdown("### Location")
colA, colB = st.columns([2,3])
with colA:
    geolocation_component(ui_t("get_location", st.session_state['lang']))
    st.markdown(f"**Manual coords:** {lat_manual:.6f}, {lon_manual:.6f}")
with colB:
    city_input = st.text_input(ui_t("enter_city", st.session_state['lang']))
    
    if city_input:
        try:
            geo = requests.get(f"https://api.openweathermap.org/geo/1.0/direct?q={city_input}&limit=1&appid={OPENWEATHER_KEY}", timeout=8).json()
            if geo:
                st.session_state['coords'] = {'lat': float(geo[0]['lat']), 'lon': float(geo[0]['lon'])}
                st.markdown(
                f"<div style='color:#000;font-weight:600;'>Using coords for {city_input}: "
                f"{geo[0]['lat']:.6f}, {geo[0]['lon']:.6f}</div>",
                unsafe_allow_html=True
            )
            else:
                st.warning("City not found (OpenWeather geocoding).")
        except Exception as e:
            st.error("Geocoding failed: " + str(e))

# capture posted message from geolocation (some Streamlit versions expose it differently)
# We won't depend on it here; users can click "Use Manual Coordinates" to set coords explicitly.

if st.session_state.get('coords') is None:
    # Try IP geolocation fallback (fast)
    try:
        ipinfo = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat_ip, lon_ip = map(float, ipinfo['loc'].split(','))
    except Exception:
        lat_ip, lon_ip = lat_manual, lon_manual
    display_lat, display_lon = lat_ip, lon_ip
else:
    display_lat = st.session_state['coords']['lat']
    display_lon = st.session_state['coords']['lon']

# ----------------------------
# Weather + Forecast helpers
# ----------------------------
def get_current_weather(lat, lon, api_key=OPENWEATHER_KEY):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        return {
            "city": data.get("name",""),
            "country": data.get("sys",{}).get("country",""),
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"],
            "desc": data["weather"][0]["description"].title(),
            "rain_1h": data.get("rain", {}).get("1h", 0),
            "cod": data.get("cod",200)
        }
    except Exception:
        return None

def get_forecast(lat, lon, api_key=OPENWEATHER_KEY):
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def derive_risk_from_weather(weather):
    if not weather:
        return "Unknown", ["Weather data unavailable"]
    rain = weather.get("rain_1h", 0)
    reasons = []
    level = "Low"
    if rain >= 50:
        level = "High"
        reasons.append(f"Very heavy recent rainfall: {rain} mm/h")
    elif rain >= 20:
        level = "Moderate"
        reasons.append(f"Significant recent rainfall: {rain} mm/h")
    else:
        reasons.append("No heavy rainfall detected in last hour")
    # city-based bump
    flood_prone = ["Mumbai","Chennai","Kolkata","Guwahati","Patna"]
    if weather.get("city") in flood_prone and weather.get("rain_1h",0) >= 5:
        level = "High"
        reasons.append(f"{weather.get('city')} is flood-prone; small rains can escalate")
    return level, reasons

# ----------------------------
# Safe Zone Locator Functions
# ----------------------------
def find_nearby_shelters(lat, lon, radius_km=10):
    """Generate nearby shelters based on the current location"""
    shelters = []
    num_shelters = np.random.randint(5, 9)
    for i in range(num_shelters):
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.random.uniform(0.5, radius_km) / 111  # Convert km to degrees
        shelter_lat = lat + distance * np.cos(angle)
        shelter_lon = lon + distance * np.sin(angle)
        shelter_types = ["School", "Community Center", "Hospital", "Government Building", "Religious Center"]
        names = ["Central", "North", "South", "East", "West", "Public", "Community"]
        shelter_type = np.random.choice(shelter_types)
        name_prefix = np.random.choice(names)
        shelters.append({
            "name": f"{name_prefix} {shelter_type}",
            "lat": shelter_lat,
            "lon": shelter_lon,
            "type": shelter_type,
            "capacity": np.random.randint(50, 501),
            "occupancy": np.random.randint(0, 401),
            "distance_km": round(distance * 111, 1)  # Convert back to km
        })
    shelters.sort(key=lambda x: x["distance_km"])
    return shelters

def get_evacuation_routes(lat, lon, shelters):
    """Generate evacuation routes to the nearest shelters"""
    routes = []
    for i, shelter in enumerate(shelters[:3]):  # Top 3 nearest shelters
        routes.append({
            "shelter": shelter["name"],
            "distance": shelter["distance_km"],
            "direction": calculate_direction(lat, lon, shelter["lat"], shelter["lon"]),
            "estimated_time": f"{int(shelter['distance_km'] * 2.5)} min"
        })
    return routes

def calculate_direction(lat1, lon1, lat2, lon2):
    """Calculate cardinal direction from point 1 to point 2"""
    d_lon = lon2 - lon1
    x = np.cos(np.radians(lat2)) * np.sin(np.radians(d_lon))
    y = np.cos(np.radians(lat1)) * np.sin(np.radians(lat2)) - np.sin(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.cos(np.radians(d_lon))
    bearing = np.arctan2(x, y)
    bearing = np.degrees(bearing)
    bearing = (bearing + 360) % 360
    directions = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
    index = round(bearing / 45) % 8
    return directions[index]

# ----------------------------
# Emergency Contacts Data
# ----------------------------
def get_emergency_contacts(lang_code='en'):
    contacts = {
        "national": [
            {"name": "National Disaster Response Force", "number": "1070"},
            {"name": "Police", "number": "100"},
            {"name": "Ambulance", "number": "102"},
            {"name": "Fire Department", "number": "101"}
        ],
        "local": [
            {"name": "Local Flood Helpline", "number": "+91-XXX-XXXX-XXX"},
            {"name": "District Emergency Officer", "number": "+91-XXX-XXXX-XXX"},
            {"name": "Rescue Team", "number": "+91-XXX-XXXX-XXX"}
        ]
    }
    if lang_code != 'en' and GT_AVAILABLE:
        for category in contacts:
            for contact in contacts[category]:
                try:
                    contact["name"] = TRANSLATOR.translate(contact["name"], dest=lang_code).text
                except:
                    pass
    return contacts

# ----------------------------
# MAIN DASHBOARD - dynamic update
# ----------------------------
st.markdown("---")
st.header("Dashboard")

# Use coordinates: prefer session coords; else ip fallback
if st.session_state.get('coords'):
    lat0 = st.session_state['coords']['lat']
    lon0 = st.session_state['coords']['lon']
else:
    try:
        ipinfo = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat0, lon0 = map(float, ipinfo['loc'].split(','))
    except Exception:
        lat0, lon0 = lat_manual, lon_manual

# Get weather and forecast for this location
weather = get_current_weather(lat0, lon0)
forecast = get_forecast(lat0, lon0)

# Dynamic Flood Summary
st.subheader(ui_t("area_summary", st.session_state['lang']))
if weather:
    risk_level, risk_reasons = derive_risk_from_weather(weather)
    summary_en = f"Current weather in {weather.get('city','Area')}: {weather.get('desc')}. Temperature: {weather.get('temp')}°C. Rain (1h): {weather.get('rain_1h',0)} mm. Flood risk: {risk_level}."
    if GT_AVAILABLE:
        try:
            trans = TRANSLATOR.translate(summary_en, dest=st.session_state['lang'])
            summary_text = trans.text
        except Exception:
            summary_text = summary_en
    else:
        summary_text = summary_en
    css_class = "alert-danger" if risk_level=="High" else "alert-warning" if risk_level=="Moderate" else "alert-safe"
    st.markdown(f'<div class="alert-banner {css_class}">{summary_text}<br><small>{" • ".join(risk_reasons)}</small></div>', unsafe_allow_html=True)
else:
    st.info("Weather data not available for this location.")

# Top stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    wl_val = round(4.2 + np.random.normal(0,0.07),2)
    st.markdown(f'<div class="stat-card"><h4>Water Level</h4><div style="font-size:28px;font-weight:700;">{wl_val} m</div><div style="color:#ea4335;">+0.3m since yesterday</div></div>', unsafe_allow_html=True)
with col2:
    rain_val = weather.get('rain_1h',0) if weather else 0
    st.markdown(f'<div class="stat-card"><h4>Rain (1h)</h4><div style="font-size:28px;font-weight:700;">{rain_val} mm</div><div style="color:#666;">Recent</div></div>', unsafe_allow_html=True)
with col3:
    alerts_count = 3 if (weather and derive_risk_from_weather(weather)[0]=="High") else 2 if (weather and derive_risk_from_weather(weather)[0]=="Moderate") else 1
    st.markdown(f'<div class="stat-card"><h4>Active Alerts</h4><div style="font-size:28px;font-weight:700;">{alerts_count}</div><div style="color:#666;">Updated</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="stat-card"><h4>Nearby Shelters</h4><div style="font-size:28px;font-weight:700;">{len([1,2,3,4])}</div><div style="color:#666;">Within 10 km</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Map area: centered to lat0, lon0 and colored circle for risk
st.subheader(ui_t("flood_monitoring_map", st.session_state['lang']))

m = folium.Map(location=[lat0, lon0], zoom_start=13 if not battery_saver else 12, control_scale=True)
folium.Marker([lat0, lon0], popup="Selected Location", icon=folium.Icon(color="blue", icon="user")).add_to(m)
shelters_demo = [
    {"name":"Central High School","lat":lat0+0.003,"lon":lon0+0.004,"cap":500,"occ":320},
    {"name":"Community Center","lat":lat0-0.004,"lon":lon0-0.003,"cap":300,"occ":150},
    {"name":"City Hospital","lat":lat0+0.006,"lon":lon0-0.002,"cap":200,"occ":180}
]
for s in shelters_demo:
    folium.Marker([s['lat'], s['lon']], popup=f"{s['name']} (Cap: {s['cap']}, Occ: {s['occ']})", icon=folium.Icon(color="green", icon="home")).add_to(m)
if weather:
    color_map = {"High":"#ea4335","Moderate":"#fbbc05","Low":"#34a853"}
    folium.Circle([lat0, lon0], radius=3500 if risk_level=="High" else 2000 if risk_level=="Moderate" else 1200,
                  color=color_map.get(risk_level,"#34a853"), fill=True, fill_opacity=0.25).add_to(m)

try:
    st_folium(m, width=900, height=500)
except Exception:
    st.error("Map requires streamlit-folium. Please install `streamlit-folium` to view interactive map.")
    st.write(pd.DataFrame(shelters_demo))

# ----------------------------
# SAFE ZONE LOCATOR - Activated Feature anchor
# ----------------------------
st.markdown("---")
st.markdown('<div id="safe-zone-locator" class="section-anchor"></div>', unsafe_allow_html=True)
st.subheader(ui_t("safe_zone_locator", st.session_state['lang']))

# Search for nearby shelters
if st.button(ui_t("search_shelters", st.session_state['lang'])):
    with st.spinner(translate_text("Searching for nearby shelters...", st.session_state['lang'])):
        time.sleep(1)
        nearby_shelters = find_nearby_shelters(lat0, lon0)
        evacuation_routes = get_evacuation_routes(lat0, lon0, nearby_shelters)
        st.markdown(f"### {translate_text('Nearby Shelters', st.session_state['lang'])}")
        for i, shelter in enumerate(nearby_shelters[:5]):
            availability = shelter['capacity'] - shelter['occupancy']
            status_color = "#34a853" if availability > 50 else "#fbbc05" if availability > 10 else "#ea4335"
            st.markdown(f"""
            <div class="shelter-item">
                <h4>{shelter['name']} ({shelter['type']})</h4>
                <p>Distance: {shelter['distance_km']} km • Capacity: {shelter['capacity']} • Occupancy: {shelter['occupancy']}</p>
                <p style="color: {status_color}; font-weight: bold;">Available space: {availability} people</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f"### {translate_text('Recommended Evacuation Routes', st.session_state['lang'])}")
        for route in evacuation_routes:
            st.markdown(f"""
            <div class="shelter-item">
                <h4>{route['shelter']}</h4>
                <p>Distance: {route['distance']} km • Direction: {route['direction']} • Est. Time: {route['estimated_time']}</p>
            </div>
            """, unsafe_allow_html=True)

# ----------------------------
# EMERGENCY CONTACTS - Activated Feature anchor
# ----------------------------
st.markdown("---")
st.markdown('<div id="emergency-contacts" class="section-anchor"></div>', unsafe_allow_html=True)
st.subheader(ui_t("emergency_contacts", st.session_state['lang']))

emergency_contacts = get_emergency_contacts(st.session_state['lang'])
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### National Emergency Numbers")
    for contact in emergency_contacts['national']:
        st.markdown(f"**{contact['name']}**: {contact['number']}")
with col2:
    st.markdown("#### Local Emergency Contacts")
    for contact in emergency_contacts['local']:
        st.markdown(f"**{contact['name']}**: {contact['number']}")

if st.button(translate_text("Show Emergency Call Instructions", st.session_state['lang'])):
    st.markdown(f"""
    <div style="color:black; background-color:#f0f0f0; padding:10px; border-radius:5px;">
        {translate_text("In a real emergency, dial the numbers above. Save these numbers in your phone for quick access.", st.session_state['lang'])}
    </div>
    """, unsafe_allow_html=True)


# ----------------------------
# EVACUATION ROUTES - Activated Feature anchor
# ----------------------------
st.markdown("---")
st.markdown('<div id="evacuation-routes" class="section-anchor"></div>', unsafe_allow_html=True)
st.subheader(ui_t("evacuation_routes", st.session_state['lang']))

if weather:
    if risk_level == "High":
        st.markdown(f"""
        <div style="color:black; background-color:#ffcccc; padding:10px; border-radius:5px;">
            <strong>🚨 HIGH RISK:</strong> {translate_text("Immediate evacuation recommended. Follow these steps:", st.session_state['lang'])}
        </div>
        """, unsafe_allow_html=True)
        advice = [
            translate_text("1. Gather essential items: documents, medicines, water, flashlight", st.session_state['lang']),
            translate_text("2. Turn off electricity and gas at the main valves", st.session_state['lang']),
            translate_text("3. Move to higher ground or designated shelter immediately", st.session_state['lang']),
            translate_text("4. Avoid walking through moving water", st.session_state['lang']),
            translate_text("5. Do not attempt to drive through flooded areas", st.session_state['lang'])
        ]
    elif risk_level == "Moderate":
        st.markdown(f"""
        <div style="color:black; background-color:#fff3cd; padding:10px; border-radius:5px;">
            <strong>⚠️ MODERATE RISK:</strong> {translate_text("Prepare for possible evacuation. Recommended actions:", st.session_state['lang'])}
        </div>
        """, unsafe_allow_html=True)
        advice = [
            translate_text("1. Prepare an emergency kit with essential supplies", st.session_state['lang']),
            translate_text("2. Identify safe routes to higher ground or shelters", st.session_state['lang']),
            translate_text("3. Monitor weather updates regularly", st.session_state['lang']),
            translate_text("4. Secure important documents in waterproof containers", st.session_state['lang']),
            translate_text("5. Charge all electronic devices", st.session_state['lang'])
        ]
    else:
        st.markdown(f"""
        <div style="color:black; background-color:#d4edda; padding:10px; border-radius:5px;">
            <strong>✅ LOW RISK:</strong> {translate_text("No immediate evacuation needed. Stay informed:", st.session_state['lang'])}
        </div>
        """, unsafe_allow_html=True)
        advice = [
            translate_text("1. Stay updated with weather forecasts", st.session_state['lang']),
            translate_text("2. Know your evacuation routes and shelter locations", st.session_state['lang']),
            translate_text("3. Prepare an emergency kit as a precaution", st.session_state['lang']),
            translate_text("4. Sign up for local emergency alerts", st.session_state['lang']),
            translate_text("5. Identify the safest areas of your home on higher floors", st.session_state['lang'])
        ]
else:
    advice = [translate_text("Weather data not available to provide evacuation guidance.", st.session_state['lang'])]

# Render advice list in black
for item in advice:
    st.markdown(f"<div style='color:black;'>{item}</div>", unsafe_allow_html=True)


# ----------------------------
# Analytics: Forecast charts using OpenWeather forecast data
# ----------------------------
st.markdown("---")
st.subheader("Analytics (Rain Forecast & Simple Insights)")

if forecast and 'list' in forecast:
    points = forecast['list'][:12]
    times = [datetime.fromtimestamp(p['dt']) for p in points]
    rains = [p.get('rain', {}).get('3h', 0) for p in points]
    temps = [p['main']['temp'] for p in points]
    df_fore = pd.DataFrame({"time": times, "rain_mm": rains, "temp": temps})
    fig1 = px.bar(df_fore, x="time", y="rain_mm", title="Rain Forecast (next ~36 hours, per 3h)", labels={"rain_mm":"Rain (mm)"})
    st.plotly_chart(fig1, use_container_width=True)
    fig2 = px.line(df_fore, x="time", y="temp", markers=True, title="Temperature Forecast (next ~36 hours)")
    st.plotly_chart(fig2, use_container_width=True)
    high_slots = sum(1 for r in rains if r >= 5)
    med_slots = sum(1 for r in rains if 1 <= r < 5)
    low_slots = sum(1 for r in rains if r == 0)
    df_pie = pd.DataFrame({"category":["High (>=5mm)","Medium (1-5mm)","Low (0mm)"], "count":[high_slots, med_slots, low_slots]})
    fig_pie = px.pie(df_pie, names="category", values="count", title="Rain Intensity Slots in Forecast")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.warning("Forecast data not available. Try again later or check your API key / network.")

# ----------------------------
# Safety guidelines (translated) and features grid
# ----------------------------
st.markdown("---")
st.subheader(translate_text("Safety Guidelines", st.session_state['lang']))
guidelines_en = [
    "Before: Prepare an emergency kit, store food & water, move valuables to higher ground.",
    "During: Move to higher ground, avoid walking through flood water, avoid electrical hazards.",
    "After: Avoid flood water, disinfect surfaces, check for structural damage."
]
if GT_AVAILABLE:
    guidelines_trans = [TRANSLATOR.translate(g, dest=st.session_state['lang']).text if st.session_state['lang']!='en' else g for g in guidelines_en]
else:
    guidelines_trans = guidelines_en
for g in guidelines_trans:
    st.write("• " + g)

st.subheader("Emergency Features")
# NOTE: The duplicate "Emergency Features" section that used to appear in main content
# has been removed per your request. Sidebar links remain the single place to access those features.

# ----------------------------
# Recent Alerts (demo) - anchor for View Alerts
# ----------------------------
st.markdown("---")
st.markdown('<div id="view-alerts" class="section-anchor"></div>', unsafe_allow_html=True)
st.subheader(translate_text("Recent Alerts", st.session_state['lang']))
demo_alerts = [
    {'type':'danger','title':'Flood Warning','message':'Heavy rainfall expected in next 24 hours'},
    {'type':'warning','title':'River Overflow','message':'River level rising above warning mark'},
    {'type':'info','title':'Shelter Opened','message':'New shelter active at City College'}
]
for a in demo_alerts:
    cls = "alert-danger" if a['type']=='danger' else "alert-warning" if a['type']=='warning' else "alert-safe"
    title_t = translate_text(a['title'], st.session_state['lang'])
    msg_t = translate_text(a['message'], st.session_state['lang'])
    st.markdown(f'<div class="alert-banner {cls}"><strong>{title_t}</strong><div style="margin-top:6px;">{msg_t}</div></div>', unsafe_allow_html=True)

# ----------------------------
# SOS button (WhatsApp link) and floating visual SOS - add SOS anchor above
# ----------------------------
st.markdown("---")
st.markdown('<div id="sos-section" class="section-anchor"></div>', unsafe_allow_html=True)
st.subheader(translate_text("SOS", st.session_state['lang']))
if st.button(translate_text("🚨 Send SOS via WhatsApp", st.session_state['lang']), key="send_sos"):
    if st.session_state.get('coords'):
        la = st.session_state['coords']['lat']
        lo = st.session_state['coords']['lon']
        msg = f"🚨 SOS! I need help. My location: https://www.google.com/maps?q={la},{lo}"
    else:
        msg = "🚨 SOS! I need help. (location unavailable)"
    wa_link = "https://wa.me/?text=" + requests.utils.quote(msg)
    st.markdown(f"[Open WhatsApp to send SOS]({wa_link})")

# Floating SOS visual button (red gradient)
st.markdown(f'<div class="sos-button">SOS</div>', unsafe_allow_html=True)

