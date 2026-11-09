# ============================================================
# GEOGUARD ID - LANDSLIDE MONITORING PROTOTYPE
# Versi standalone: simulasi data, visualisasi 3D, dan notifikasi Telegram.
# Belum terhubung ke hardware/ESP32.
# Jalankan: streamlit run GeoGuard_ID_Earth_Water.py
# ============================================================

import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ------------------------- PAGE CONFIG -------------------------
st.set_page_config(
    page_title="GeoGuard ID | Landslide Intelligence",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------- STYLE -------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'DM Sans', sans-serif;
        color: #17251f;
    }
    .stApp {
        background:
            radial-gradient(circle at 88% 4%, rgba(73, 151, 157, .13), transparent 25rem),
            linear-gradient(145deg, #f4f0e6 0%, #edf4ef 52%, #eaf3f4 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(175deg, #173b32 0%, #153b43 100%);
        border-right: 1px solid rgba(255,255,255,.10);
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
        opacity: 1;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
        color: #E7F0EC !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] [data-testid="stSlider"] *,
    [data-testid="stSidebar"] [data-testid="stMetric"] * {
        color: #FFFFFF !important;
        opacity: 1 !important;
    }

    /* Kolom pencarian dan seluruh input dibuat gelap agar terbaca. */
    .stTextInput input, .stTextArea textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        color: #17251f !important;
        -webkit-text-fill-color: #17251f !important;
        background-color: #ffffff !important;
        caret-color: #17251f !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #718078 !important;
        -webkit-text-fill-color: #718078 !important;
        opacity: 1 !important;
    }
    [data-testid="stWidgetLabel"] p,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] {
        color: #34483f;
    }
    [data-testid="stSidebar"] .stTextInput input {
        color: #17251f !important;
        -webkit-text-fill-color: #17251f !important;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 30px 32px;
        border-radius: 22px;
        background:
            radial-gradient(circle at 90% 15%, rgba(111, 190, 190, .34), transparent 13rem),
            radial-gradient(circle at 78% 110%, rgba(177, 139, 91, .30), transparent 16rem),
            linear-gradient(115deg, #183b31 0%, #205548 52%, #1b5964 100%);
        color: #ffffff;
        margin-bottom: 20px;
        box-shadow: 0 12px 30px rgba(24, 59, 49, .15);
        border: 1px solid rgba(255,255,255,.14);
    }
    .hero h1 { color: #ffffff !important; margin: 0; font-size: 2.1rem; font-weight: 800; }
    .hero p { color: #e0eee7 !important; margin: 8px 0 0 0; }
    .hero .hero-tag {
        display: inline-block; margin-top: 15px; padding: 6px 11px;
        border: 1px solid rgba(255,255,255,.25); border-radius: 30px;
        color: #e9f5ef; background: rgba(255,255,255,.10); font-size: .76rem;
    }

    .metric-card {
        background: rgba(255,255,255,.94);
        padding: 18px 20px; border-radius: 16px;
        border: 1px solid #dce7dd;
        box-shadow: 0 5px 18px rgba(37, 71, 57, .06);
        min-height: 112px;
    }
    .metric-label { color:#607469; font-size:.85rem; font-weight:700; letter-spacing:.02em; }
    .metric-value { color:#183b31; font-size:1.8rem; font-weight:800; margin-top:5px; }
    .metric-note { color:#718078; font-size:.78rem; margin-top:3px; }
    .section-title { color:#183b31; font-size:1.15rem; font-weight:800; margin: 8px 0 12px 0; }
    .small-note { color:#607469; font-size:.82rem; }
    .status-pill { padding:7px 12px; border-radius:30px; font-weight:800; display:inline-block; }

    div.stButton > button, div.stDownloadButton > button {
        border-radius: 11px;
        border: 1px solid #2c6654;
        background: linear-gradient(110deg, #245743, #27717a);
        color: #ffffff;
        font-weight: 700;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        border-color: #1a493b;
        background: #1a493b;
        color: #ffffff;
    }
    [data-testid="stMetric"] {
        background: rgba(255,255,255,.72);
        border: 1px solid #dce7dd;
        border-radius: 13px;
        padding: 12px 14px;
    }
    [data-testid="stTabs"] button { color: #29483b; font-weight: 700; }
    hr { border-color: #d7e2d9; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------- SESSION STATE -------------------------
defaults = {
    "rain": 0.0,
    "rainfall_hourly": None,
    "rainfall_updated_at": None,
    "moisture": 42.0,
    "slope": 32.0,
    "depth": 2.0,
    "cohesion": 18.0,
    "friction": 28.0,
    "unit_weight": 18.0,
    "location_name": "Magelang, Jawa Tengah",
    "latitude": -7.4706,
    "longitude": 110.2178,
    "telegram_enabled": False,
    "last_alert_status": "NORMAL",
    "last_alert_time": 0.0,
    "last_alert_attempt_time": 0.0,
    "reports": [],
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ------------------------- HELPERS -------------------------
def calculate_fos(c, phi_deg, beta_deg, depth_m, gamma, moisture_pct, rainfall_mm):
    """
    Model infinite-slope sederhana untuk demonstrasi akademik.
    Kadar air dan hujan dipakai sebagai indeks simulasi tekanan air,
    bukan pengukuran tekanan pori atau derajat kejenuhan aktual.
    """
    beta = np.radians(float(beta_deg))
    phi = np.radians(float(phi_deg))
    z = max(float(depth_m), 0.1)
    gamma = max(float(gamma), 1.0)

    # Indeks tekanan air sederhana untuk demonstrasi, bukan model infiltrasi.
    moisture_index = np.clip(float(moisture_pct) / 100.0, 0.0, 1.0)
    rain_index = np.clip(float(rainfall_mm) / 250.0, 0.0, 1.0)
    pore_pressure_index = np.clip(0.65 * moisture_index + 0.35 * rain_index, 0.0, 0.95)

    normal_stress = gamma * z * (np.cos(beta) ** 2)
    pore_pressure = pore_pressure_index * normal_stress
    driving_stress = gamma * z * np.sin(beta) * np.cos(beta)

    resisting_stress = float(c) + max(normal_stress - pore_pressure, 0.0) * np.tan(phi)
    fos = resisting_stress / max(driving_stress, 0.01)
    return float(fos), float(pore_pressure), float(pore_pressure_index)


@st.cache_data(ttl=900, show_spinner=False)
def get_open_meteo_rainfall(latitude, longitude):
    """Ambil curah hujan per jam dari Open-Meteo untuk koordinat aktif.

    Akumulasi 24 jam dihitung dari data hourly yang waktunya tidak melewati
    waktu lokal saat ini. API menyediakan data model cuaca, bukan pengukuran
    langsung dari penakar hujan di titik koordinat tersebut.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": round(float(latitude), 5),
        "longitude": round(float(longitude), 5),
        "hourly": "rain",
        "current": "rain",
        "past_days": 2,
        "forecast_days": 1,
        "timezone": "Asia/Jakarta",
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()

    hourly = payload.get("hourly", {})
    if not hourly.get("time") or "rain" not in hourly:
        raise ValueError("Data hujan per jam tidak tersedia dari Open-Meteo.")

    frame = pd.DataFrame({
        "Waktu": pd.to_datetime(hourly["time"]),
        "Curah hujan (mm/jam)": pd.to_numeric(hourly["rain"], errors="coerce"),
    }).dropna(subset=["Curah hujan (mm/jam)"]).sort_values("Waktu")

    now_local = datetime.now(ZoneInfo("Asia/Jakarta")).replace(tzinfo=None)
    last_24h = frame[(frame["Waktu"] <= now_local) & (frame["Waktu"] > now_local - timedelta(hours=24))].copy()
    if last_24h.empty:
        raise ValueError("Open-Meteo belum mengembalikan data hujan 24 jam terakhir untuk lokasi ini.")

    rainfall_24h = float(last_24h["Curah hujan (mm/jam)"].fillna(0).sum())
    latest_time = last_24h["Waktu"].max()
    current_row = last_24h.iloc[-1]
    return {
        "rain_24h": rainfall_24h,
        "hourly_24h": last_24h.tail(24).reset_index(drop=True),
        "latest_time": latest_time.strftime("%d-%m-%Y %H:%M WIB"),
        "latest_hour_rain": float(current_row["Curah hujan (mm/jam)"]),
        "timezone": payload.get("timezone", "Asia/Jakarta"),
    }


def classify_status(fos):
    # Ambang hanya untuk demonstrasi UI, bukan standar keputusan evakuasi.
    if fos < 1.0:
        return "BAHAYA (SIAGA 1)", "#dc2626", "danger"
    if fos < 1.25:
        return "SIAGA 2", "#ea580c", "warning"
    if fos < 1.5:
        return "WASPADA", "#ca8a04", "warning"
    return "NORMAL", "#15803d", "success"


def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def send_telegram(message):
    """Telegram opsional. Token disimpan di .streamlit/secrets.toml."""
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
    except Exception:
        return False, "Konfigurasi Telegram belum dibuat."

    if not token or not chat_id:
        return False, "Bot token atau chat ID masih kosong."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(
            url,
            data={"chat_id": chat_id, "text": message},
            timeout=12,
        )
        payload = response.json()
        if response.ok and payload.get("ok"):
            return True, "Pesan Telegram berhasil dikirim."
        return False, payload.get("description", "Telegram menolak permintaan.")
    except requests.RequestException as exc:
        return False, f"Koneksi Telegram gagal: {exc}"
    except ValueError:
        return False, "Respons Telegram tidak dapat dibaca."


def build_alert_message(status, fos, rain, moisture, location):
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    if status == "BAHAYA (SIAGA 1)":
        action = "Indikator simulasi menunjukkan kondisi kritis. Jauhi area lereng dan ikuti arahan petugas/BPBD."
        title = "🚨 PERINGATAN SIMULASI LONGSOR"
    else:
        action = "Tingkatkan pemantauan dan periksa kondisi lereng oleh petugas berwenang."
        title = "⚠️ PERINGATAN SIAGA LERENG"
    return (
        f"{title}\n"
        f"GeoGuard ID - Prototype\n"
        f"Waktu: {now}\n"
        f"Lokasi: {location}\n"
        f"Status simulasi: {status}\n"
        f"FoS simulasi: {fos:.2f}\n"
        f"Curah hujan Open-Meteo: {rain:.1f} mm/24 jam\n"
        f"Kadar air simulasi: {moisture:.1f}%\n\n"
        f"Tindakan: {action}\n\n"
        "Catatan: Data dan status ini merupakan simulasi akademik, bukan dasar tunggal evakuasi."
    )


def geocode_location(query):
    """Pencarian nama lokasi via Nominatim/OpenStreetMap."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "GeoGuardIDPrototype/1.0 (academic demo)"}
    response = requests.get(
        url,
        params={"q": query, "format": "json", "limit": 1},
        headers=headers,
        timeout=12,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    return results[0]


def make_terrain_figure(deformation=0.0, rainfall=35.0):
    """Permukaan topografi sintetis 3D untuk visualisasi konsep."""
    x = np.linspace(-5, 5, 65)
    y = np.linspace(-4, 4, 55)
    X, Y = np.meshgrid(x, y)

    # Lereng miring dengan kontur bergelombang.
    base = 3.8 - 0.42 * X + 0.16 * np.sin(Y * 1.2) + 0.10 * np.cos(X * 1.3)
    scar = np.exp(-(((X - 0.8) / 1.8) ** 2 + ((Y + 0.1) / 1.25) ** 2))
    slide = np.exp(-(((X - 1.5) / 2.0) ** 2 + ((Y + 0.2) / 1.5) ** 2))
    Z = base - float(deformation) * 1.15 * slide + 0.10 * scar

    fig = go.Figure()
    fig.add_trace(
        go.Surface(
            x=X, y=Y, z=Z,
            colorscale="Earth",
            colorbar=dict(title="Elevasi<br>relatif"),
            opacity=0.96,
            name="Permukaan lereng",
            hovertemplate="X: %{x:.1f}<br>Y: %{y:.1f}<br>Elevasi relatif: %{z:.2f}<extra></extra>",
        )
    )

    # Bidang gelincir konseptual.
    slip_z = 2.35 - 0.42 * X + 0.05 * np.sin(Y)
    mask = ((X - 0.8) / 2.0) ** 2 + ((Y + 0.1) / 1.5) ** 2 < 1.0
    slip_z = np.where(mask, slip_z, np.nan)
    fig.add_trace(
        go.Surface(
            x=X, y=Y, z=slip_z,
            colorscale=[[0, "#e63946"], [1, "#e63946"]],
            showscale=False,
            opacity=0.72,
            name="Bidang gelincir konseptual",
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis_title="Jarak X (relatif)",
            yaxis_title="Jarak Y (relatif)",
            zaxis_title="Elevasi relatif",
            aspectratio=dict(x=1.35, y=1, z=0.65),
            camera=dict(eye=dict(x=1.55, y=1.55, z=1.0)),
        ),
        legend=dict(orientation="h", y=1.02, x=0),
    )
    return fig


def make_cross_section(deformation=0.0, rainfall=35.0):
    x = np.linspace(0, 100, 250)
    ground = 42 - 0.34 * x + 2.5 * np.sin(x / 12)
    slip = 25 - 0.25 * x + 1.5 * np.sin(x / 18)
    moved = np.clip(float(deformation), 0, 1)
    ground_after = ground - moved * 5 * np.exp(-((x - 63) / 18) ** 2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=ground, mode="lines", name="Permukaan awal",
        line=dict(color="#315f46", width=3),
        fill="tozeroy", fillcolor="rgba(91,145,102,.18)"
    ))
    fig.add_trace(go.Scatter(
        x=x, y=ground_after, mode="lines", name="Permukaan simulasi",
        line=dict(color="#d97706", width=3, dash="dash")
    ))
    fig.add_trace(go.Scatter(
        x=x, y=slip, mode="lines", name="Bidang gelincir ilustratif",
        line=dict(color="#dc2626", width=2, dash="dot")
    ))
    fig.add_annotation(
        x=18, y=ground[45] + 4, text=f"Infiltrasi hujan: {rainfall:.0f} mm/24 jam",
        showarrow=True, arrowhead=2, ax=15, ay=-35
    )
    fig.update_layout(
        height=370, margin=dict(l=10, r=10, t=25, b=10),
        xaxis_title="Jarak horizontal (m, skematis)",
        yaxis_title="Elevasi (m, skematis)",
        legend=dict(orientation="h", y=1.12),
    )
    return fig


# ------------------------- SIDEBAR -------------------------
with st.sidebar:
    st.markdown("## ⛰️ GeoGuard ID")
    st.caption("Landslide Intelligence Prototype")
    st.markdown("---")
    st.markdown("### 📍 Lokasi pemantauan")
    location_query = st.text_input(
        "Cari nama lokasi",
        placeholder="Contoh: Kecamatan Kaliangkrik, Magelang",
    )
    if st.button("Cari lokasi", use_container_width=True):
        if location_query.strip():
            try:
                found = geocode_location(location_query.strip())
                if found:
                    st.session_state.latitude = float(found["lat"])
                    st.session_state.longitude = float(found["lon"])
                    st.session_state.location_name = found.get("display_name", location_query)
                    st.success("Lokasi ditemukan.")
                else:
                    st.warning("Lokasi tidak ditemukan. Coba nama yang lebih spesifik.")
            except Exception as exc:
                st.error(f"Pencarian lokasi gagal: {exc}")
        else:
            st.warning("Masukkan nama lokasi terlebih dahulu.")

    st.caption(f"Lokasi aktif: {st.session_state.location_name}")
    st.caption(f"Koordinat: {st.session_state.latitude:.5f}, {st.session_state.longitude:.5f}")
    st.markdown("---")
    st.markdown("### 🌧️ Data hujan Open-Meteo")
    if st.button("🔄 Perbarui data hujan", use_container_width=True):
        get_open_meteo_rainfall.clear()
        st.rerun()

    try:
        rainfall_data = get_open_meteo_rainfall(
            st.session_state.latitude, st.session_state.longitude
        )
        rain = float(rainfall_data["rain_24h"])
        st.session_state.rain = rain
        st.session_state.rainfall_hourly = rainfall_data["hourly_24h"]
        st.session_state.rainfall_updated_at = rainfall_data["latest_time"]
        st.metric("Akumulasi hujan 24 jam", f"{rain:.1f} mm")
        st.caption(f"Data terakhir: {rainfall_data['latest_time']}")
        st.caption("Sumber: Open-Meteo Weather Forecast API · estimasi model cuaca berdasarkan koordinat (bukan sensor hujan lokal)")
    except (requests.RequestException, ValueError, KeyError) as exc:
        st.session_state.rainfall_hourly = None
        st.error(f"Data Open-Meteo gagal diambil: {exc}")
        st.warning("Perhitungan dihentikan agar aplikasi tidak mengganti data hujan dengan angka dummy.")
        st.stop()

    st.markdown("---")
    st.markdown("### 🎛️ Parameter simulasi")
    moisture = st.slider("Indeks kadar air (%)", 5.0, 100.0, float(st.session_state.moisture), 1.0)
    slope = st.slider("Sudut lereng (°)", 10.0, 60.0, float(st.session_state.slope), 1.0)
    depth = st.slider("Kedalaman bidang gelincir (m)", 0.5, 8.0, float(st.session_state.depth), 0.1)
    cohesion = st.slider("Kohesi tanah c (kPa)", 1.0, 50.0, float(st.session_state.cohesion), 1.0)
    friction = st.slider("Sudut geser dalam φ (°)", 10.0, 45.0, float(st.session_state.friction), 1.0)
    unit_weight = st.slider("Berat isi tanah γ (kN/m³)", 14.0, 22.0, float(st.session_state.unit_weight), 0.5)

    st.session_state.moisture = moisture
    st.session_state.slope = slope
    st.session_state.depth = depth
    st.session_state.cohesion = cohesion
    st.session_state.friction = friction
    st.session_state.unit_weight = unit_weight

    st.markdown("---")
    st.markdown("### 📡 Status sistem")
    st.info("Curah hujan diambil dari Open-Meteo. Parameter tanah dan sensor lainnya masih berupa simulasi/input pengguna.")
    st.caption("Belum terhubung ke ESP32, sensor, relay, atau sirine fisik.")

# ------------------------- CALCULATIONS -------------------------
fos, pore_pressure, water_index = calculate_fos(
    cohesion, friction, slope, depth, unit_weight, moisture, rain
)
status, status_color, status_kind = classify_status(fos)
deformation = float(np.clip((1.55 - fos) / 1.1, 0, 1))
movement_rate = 0.4 + 5.0 * deformation + 0.012 * rain

# ------------------------- HEADER -------------------------
st.markdown(
    """
    <div class="hero">
      <h1>⛰️ GeoGuard ID</h1>
      <p>Intelligent Landslide Monitoring & Early Warning Prototype</p>\n      <span class="hero-tag">EARTH • WATER • SLOPE MONITORING</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "Dashboard demonstrasi akademik. Curah hujan bersumber dari Open-Meteo; parameter sensor/lereng, "
    "ambang status, dan bentuk longsoran lainnya masih berupa simulasi, bukan pemantauan lapangan."
)

# ------------------------- STATUS + METRICS -------------------------
left, right = st.columns([2, 1])
with left:
    st.markdown(f"### Status kondisi lereng: <span style='color:{status_color}'>{status}</span>", unsafe_allow_html=True)
with right:
    st.markdown(
        f"<div style='text-align:right;color:#64748b;font-size:.85rem'>Lokasi aktif<br><b>{st.session_state.location_name}</b></div>",
        unsafe_allow_html=True,
    )

m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card("FACTOR OF SAFETY", f"{fos:.2f}", "Hasil model simulasi")
with m2:
    metric_card("CURAH HUJAN", f"{rain:.1f} mm", "Open-Meteo · estimasi hujan 24 jam terakhir")
with m3:
    metric_card("INDEKS KADAR AIR", f"{moisture:.0f}%", "Input simulasi pengguna")
with m4:
    metric_card("LAJU PERGESERAN", f"{movement_rate:.2f} mm/jam", "Nilai ilustratif, bukan sensor")

st.markdown("")

# ------------------------- TABS -------------------------
tab_dashboard, tab_3d, tab_analysis, tab_alert, tab_reports = st.tabs(
    ["📊 Dashboard", "🧊 Simulasi 3D", "📐 Analisis", "🚨 Peringatan", "📝 Laporan warga"]
)

with tab_dashboard:
    c1, c2 = st.columns([1.35, 1])
    with c1:
        st.markdown('<div class="section-title">Peta lokasi pemantauan</div>', unsafe_allow_html=True)
        map_df = pd.DataFrame({
            "lat": [st.session_state.latitude],
            "lon": [st.session_state.longitude],
        })
        st.map(map_df, zoom=11, use_container_width=True)
        st.caption("Pin menunjukkan lokasi pencarian, bukan lokasi sensor yang telah dipasang.")
    with c2:
        st.markdown('<div class="section-title">Ringkasan kondisi</div>', unsafe_allow_html=True)
        st.metric("Tekanan air pori estimasi model", f"{pore_pressure:.1f} kPa")
        st.metric("Indeks tekanan air simulasi", f"{water_index * 100:.0f}%")
        st.metric("Sudut lereng", f"{slope:.0f}°")
        if status == "BAHAYA (SIAGA 1)":
            st.error("Indikator simulasi berada pada kategori Bahaya.")
        elif status == "SIAGA 2":
            st.warning("Indikator simulasi berada pada kategori Siaga 2.")
        elif status == "WASPADA":
            st.warning("Indikator simulasi berada pada kategori Waspada.")
        else:
            st.success("Indikator simulasi berada pada kategori Normal.")

    st.markdown('<div class="section-title">Tren curah hujan Open-Meteo 24 jam terakhir</div>', unsafe_allow_html=True)
    rain_history = st.session_state.rainfall_hourly
    if rain_history is not None and not rain_history.empty:
        rain_fig = go.Figure()
        rain_fig.add_trace(go.Bar(
            x=rain_history["Waktu"],
            y=rain_history["Curah hujan (mm/jam)"],
            name="Hujan per jam",
            marker_color="#168b83",
        ))
        rain_fig.update_layout(
            height=300, margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="Waktu (WIB)", yaxis_title="Curah hujan (mm/jam)",
            showlegend=False,
        )
        st.plotly_chart(rain_fig, use_container_width=True)
        st.caption("Grafik memakai variabel rain dari Open-Meteo (estimasi hujan per jam berbasis model cuaca, bukan pengukuran penakar hujan di lokasi).")

    st.markdown('<div class="section-title">Indikator simulasi lainnya</div>', unsafe_allow_html=True)
    rng = np.random.default_rng(27)
    hours = np.arange(24)
    moisture_series = np.clip(moisture - 8 + np.cumsum(rng.normal(0.35, 0.5, 24)), 0, 100)
    displacement_series = np.maximum(0, np.cumsum(rng.normal(movement_rate / 24, 0.04, 24)))
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=hours, y=moisture_series, name="Indeks kadar air (simulasi)", mode="lines"))
    fig_trend.add_trace(go.Scatter(x=hours, y=displacement_series, name="Pergeseran kumulatif (simulasi)", mode="lines", yaxis="y2"))
    fig_trend.update_layout(
        height=340, margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="Jam ilustratif",
        yaxis=dict(title="Kadar air indeks (%)"),
        yaxis2=dict(title="Pergeseran (mm)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with tab_3d:
    st.markdown('<div class="section-title">Model topografi lereng 3D</div>', unsafe_allow_html=True)
    deformation_level = st.slider(
        "Tahapan deformasi visual",
        min_value=0,
        max_value=100,
        value=int(deformation * 100),
        step=5,
        key="deformation_slider",
        help="Mengubah bentuk permukaan sintetis untuk ilustrasi, bukan menghitung perpindahan nyata.",
    )
    st.plotly_chart(
        make_terrain_figure(deformation_level / 100, rain),
        use_container_width=True,
        config={"displayModeBar": True, "scrollZoom": True},
    )
    st.caption("Permukaan 3D dan bidang gelincir berwarna merah merupakan geometri sintetis untuk demonstrasi.")
    st.markdown('<div class="section-title">Penampang lereng dan bidang gelincir</div>', unsafe_allow_html=True)
    st.plotly_chart(
        make_cross_section(deformation_level / 100, rain),
        use_container_width=True,
    )
    st.caption("Penampang bersifat skematis. Untuk analisis teknik diperlukan geometri dan parameter tanah hasil investigasi.")

with tab_analysis:
    st.markdown('<div class="section-title">Analisis sensitivitas faktor keamanan</div>', unsafe_allow_html=True)
    moisture_values = np.linspace(5, 100, 30)
    fos_values = [
        calculate_fos(cohesion, friction, slope, depth, unit_weight, m, rain)[0]
        for m in moisture_values
    ]
    sensitivity = pd.DataFrame({"Indeks kadar air (%)": moisture_values, "FoS simulasi": fos_values})
    fig_sens = go.Figure()
    fig_sens.add_trace(go.Scatter(
        x=sensitivity["Indeks kadar air (%)"],
        y=sensitivity["FoS simulasi"],
        mode="lines",
        line=dict(width=3, color="#0f766e"),
        name="FoS",
    ))
    fig_sens.add_hline(y=1.0, line_dash="dash", line_color="#dc2626", annotation_text="FoS = 1,0")
    fig_sens.add_hline(y=1.5, line_dash="dot", line_color="#ca8a04", annotation_text="FoS = 1,5")
    fig_sens.update_layout(height=380, xaxis_title="Indeks kadar air (%)", yaxis_title="Factor of Safety", margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(fig_sens, use_container_width=True)

    st.markdown("#### Parameter model")
    params = pd.DataFrame({
        "Parameter": ["Kohesi", "Sudut geser dalam", "Sudut lereng", "Kedalaman", "Berat isi tanah"],
        "Nilai": [f"{cohesion:.1f} kPa", f"{friction:.1f}°", f"{slope:.1f}°", f"{depth:.1f} m", f"{unit_weight:.1f} kN/m³"],
    })
    st.dataframe(params, use_container_width=True, hide_index=True)
    st.info(
        "Catatan metodologi: perhitungan ini merupakan model infinite-slope yang disederhanakan. "
        "Curah hujan Open-Meteo merupakan estimasi cuaca berbasis model pada koordinat terpilih, "
        "sedangkan indeks kadar air bukan pengukuran tekanan pori aktual. "
        "Jangan gunakan angka FoS atau ambang aplikasi sebagai dasar keputusan keselamatan lapangan."
    )

with tab_alert:
    st.markdown('<div class="section-title">Pusat peringatan dini</div>', unsafe_allow_html=True)
    if status == "BAHAYA (SIAGA 1)":
        st.error("🚨 BAHAYA — indikator simulasi menunjukkan kondisi kritis.")
    elif status == "SIAGA 2":
        st.warning("⚠️ SIAGA 2 — pemantauan perlu ditingkatkan.")
    elif status == "WASPADA":
        st.warning("🟡 WASPADA — pantau perubahan parameter.")
    else:
        st.success("🟢 NORMAL — berdasarkan parameter simulasi saat ini.")

    st.info(
        "Peringatan ditampilkan melalui dashboard dan dapat dikirim ke Telegram. ""Seluruh indikator pada versi ini masih berupa simulasi."
    )

    st.markdown("---")
    st.markdown("#### Notifikasi Telegram")
    st.caption("Notifikasi dikirim jika bot sudah dikonfigurasi dan status simulasi berubah menjadi Waspada, Siaga 2, atau Bahaya.")
    telegram_opt_in = st.checkbox(
        "Aktifkan notifikasi Telegram otomatis",
        value=st.session_state.telegram_enabled,
        key="telegram_checkbox",
    )
    st.session_state.telegram_enabled = telegram_opt_in

    if st.button("📨 Tes kirim Telegram", use_container_width=True):
        test_message = (
            "🧪 TES NOTIFIKASI GEOGUARD ID\n"
            "Bot Telegram terhubung ke prototype GeoGuard ID.\n"
            "Pesan ini hanya pengujian, bukan peringatan bahaya."
        )
        ok, info = send_telegram(test_message)
        if ok:
            st.success(info)
        else:
            st.error(info)

    # Notifikasi otomatis saat status berubah.
    # Status alert tidak dianggap terkirim sebelum Telegram mengonfirmasi sukses.
    previous = st.session_state.last_alert_status
    is_alert = status in ("WASPADA", "SIAGA 2", "BAHAYA (SIAGA 1)")
    changed = status != previous
    now = time.time()

    # Jika kembali NORMAL, jadikan NORMAL sebagai baseline untuk transisi berikutnya.
    if status == "NORMAL":
        st.session_state.last_alert_status = "NORMAL"

    elif telegram_opt_in and is_alert and changed:
        cooldown_ok = now - st.session_state.last_alert_time >= 600
        retry_ok = now - st.session_state.last_alert_attempt_time >= 60
        escalation_to_danger = (
            status == "BAHAYA (SIAGA 1)" and previous != "BAHAYA (SIAGA 1)"
        )

        if (cooldown_ok or escalation_to_danger) and retry_ok:
            st.session_state.last_alert_attempt_time = now
            message = build_alert_message(
                status, fos, rain, moisture, st.session_state.location_name
            )
            ok, info = send_telegram(message)

            if ok:
                st.session_state.last_alert_time = now
                st.session_state.last_alert_status = status
                st.success("Notifikasi otomatis berhasil dikirim ke Telegram.")
            else:
                st.warning(
                    f"Notifikasi belum terkirim: {info} "
                    "Sistem akan mencoba kembali setelah jeda."
                )

    # Saat notifikasi dimatikan, jangan menandai status bahaya sebagai sudah terkirim.
    # Dengan begitu, mengaktifkan Telegram ketika status masih alert tetap memicu pesan.

    st.markdown("---")
    st.markdown("#### Konfigurasi Telegram")
    st.code(
        '[telegram]\nbot_token = "TOKEN_BOT_TELEGRAM"\nchat_id = "CHAT_ID_TELEGRAM"',
        language="toml",
    )
    st.caption("Buat .streamlit/secrets.toml dengan bagian [telegram], bot_token, dan chat_id. Jangan membagikan token bot. Setelah menyimpan konfigurasi, tekan tombol tes kirim Telegram.")

with tab_reports:
    st.markdown('<div class="section-title">Laporan kondisi lereng dari warga</div>', unsafe_allow_html=True)
    with st.form("report_form", clear_on_submit=True):
        reporter = st.text_input("Nama pelapor (opsional)")
        report_type = st.selectbox(
            "Jenis laporan",
            ["Retakan tanah", "Longsoran kecil", "Pohon/tiang mulai miring", "Mata air baru", "Pergerakan dinding penahan", "Lainnya"],
        )
        description = st.text_area("Deskripsi kondisi", placeholder="Jelaskan kondisi yang terlihat...")
        submitted = st.form_submit_button("Kirim laporan")
        if submitted:
            if description.strip():
                st.session_state.reports.insert(
                    0,
                    {
                        "Waktu": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                        "Pelapor": reporter.strip() or "Anonim",
                        "Jenis": report_type,
                        "Deskripsi": description.strip(),
                    },
                )
                st.success("Laporan tersimpan pada sesi aplikasi ini.")
            else:
                st.warning("Deskripsi laporan belum diisi.")

    if st.session_state.reports:
        st.dataframe(pd.DataFrame(st.session_state.reports), use_container_width=True, hide_index=True)
        report_csv = pd.DataFrame(st.session_state.reports).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Unduh laporan CSV", report_csv, "laporan_geoguard.csv", "text/csv")
    else:
        st.info("Belum ada laporan warga.")

# ------------------------- FOOTER -------------------------
st.markdown("---")
st.markdown(
    """
    <div class="small-note">
    <b>GeoGuard ID — Academic Prototype</b><br>
    Curah hujan bersumber dari Open-Meteo. Parameter sensor lain, topografi 3D, dan deformasi masih simulasi.
    Sistem belum terhubung ke perangkat IoT dan belum tervalidasi untuk pemantauan atau peringatan operasional.
    </div>
    """,
    unsafe_allow_html=True,
)
