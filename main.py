import streamlit as st
import calendar
from datetime import datetime, timedelta
import plotly.graph_objects as go
import math
from pymongo import MongoClient

# MongoDB Setup
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["kalender_db"]
coll = db["kehadiran"]

# Page setup
st.set_page_config(layout="wide")

# Sidebar Pilih Periode
st.sidebar.header("Pilih Bulan Awal")
year = st.sidebar.number_input("Tahun", min_value=1900, max_value=2100, value=datetime.now().year)
month = st.sidebar.selectbox("Bulan", list(calendar.month_name)[1:], index=datetime.now().month - 1)
month_number = list(calendar.month_name).index(month)

# Rentang Tanggal
start_date = datetime(year, month_number, 16)
end_date = datetime(year + 1, 1, 15) if month_number == 12 else datetime(year, month_number + 1, 15)
date_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

# Tanggal merah (libur nasional)
tanggal_merah = {"01-01", "17-08", "25-12", "10-04", "11-04", "12-04"}

# Load dari MongoDB
def load_kehadiran(user):
    kehadiran = {}
    for doc in coll.find({"user": user, "type": {"$ne": "catatan"}}):
        tanggal = datetime.strptime(doc["tanggal"], '%Y-%m-%d')
        kehadiran[tanggal] = doc.get("hadir", False)
    catatan_doc = coll.find_one({"user": user, "type": "catatan"})
    catatan = catatan_doc["catatan"] if catatan_doc else ""
    return kehadiran, catatan

# Simpan ke MongoDB
def simpan_kehadiran(user, kehadiran, catatan):
    records = []
    for tanggal, hadir in kehadiran.items():
        if tanggal:
            records.append({
                "user": user,
                "tanggal": tanggal.strftime('%Y-%m-%d'),
                "hadir": hadir
            })
    coll.delete_many({"user": user, "type": {"$ne": "catatan"}})
    if records:
        coll.insert_many(records)
    coll.update_one(
        {"user": user, "type": "catatan"},
        {"$set": {"catatan": catatan, "type": "catatan"}},
        upsert=True
    )

# Fungsi Kalender
def tampilkan_kalender(label_user, default_kehadiran):
    st.markdown(f"### Kehadiran {label_user}")
    days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

    today = datetime.today().date()
    hadir_dict = {}
    total_hari_kerja = 0
    hadir_sampai_hari_ini = 0

    # Susun minggu
    weeks = []
    week = [""] * 7
    for date in date_list:
        day_idx = date.weekday()
        if date == date_list[0]:
            week = [""] * day_idx
        week.append(date)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append("")
        weeks.append(week)

    # Tampilkan header hari
    cols = st.columns(7)
    for i, d in enumerate(days):
        with cols[i]:
            st.markdown(f"**{d}**")

    # Tampilkan kalender
    for week in weeks:
        cols = st.columns(7)
        for i, date in enumerate(week):
            with cols[i]:
                if date != "":
                    label = date.strftime("%d %b")
                    key = f"{label_user}_{date.strftime('%Y-%m-%d')}"
                    is_red = f"{date.day:02d}-{date.month:02d}" in tanggal_merah
                    is_sunday = date.weekday() == 6
                    if is_red or is_sunday:
                        st.markdown(f"<div style='color:red'>{label}<br><em>Libur</em></div>", unsafe_allow_html=True)
                        hadir_dict[date] = None
                    else:
                        total_hari_kerja += 1
                        default = default_kehadiran.get(date, True)
                        hadir = st.checkbox(label, key=key, value=default)
                        hadir_dict[date] = hadir
                        if date.date() <= today and hadir:
                            hadir_sampai_hari_ini += 1
                else:
                    st.markdown(" ")

    return hadir_dict, total_hari_kerja, hadir_sampai_hari_ini


# === Tabs ===
tab1, tab2, tab3 = st.tabs(["Jadwal Rizal", "Jadwal Thesi", "Rekap Bersamaan"])

# Tab Rizal
with tab1:
    default_rizal, catatan_default_rizal = load_kehadiran("Rizal")
    kehadiran_rizal, hari_kerja_rizal, hadir_sampai_hari_ini_rizal = tampilkan_kalender("Rizal", default_rizal)
    hadir_rizal = sum(1 for v in kehadiran_rizal.values() if v is True)
    min_hadir = math.ceil(hari_kerja_rizal * 0.7)
    maks_bolos = hari_kerja_rizal - min_hadir
    bolos_rizal = hari_kerja_rizal - hadir_rizal

    # st.write(f"Hadir: **{hadir_rizal}**")
    st.info(f"📅 Jumlah hadir hingga hari ini: **{hadir_sampai_hari_ini_rizal} hari**")
    st.write(f"Total hari kerja: **{hari_kerja_rizal}**")
    st.write(f"Maks bolos: **{maks_bolos}**")

    fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=bolos_rizal,
    domain={'x': [0, 1], 'y': [0, 1]},
    gauge={
        'axis': {'range': [0, hari_kerja_rizal]},
        'bar': {'color': "red"},
        'steps': [
            {'range': [0, maks_bolos], 'color': "lightgreen"},
            {'range': [maks_bolos, hari_kerja_rizal], 'color': "lightcoral"},
        ],
    },
    title={'text': "Jumlah Bolos"}
    ))
    fig.update_layout(height=350, margin=dict(t=50, b=20))
    st.plotly_chart(fig, use_container_width=True, key="rizal_gauge")


    if hadir_rizal >= min_hadir:
        st.success("✅ Target kehadiran tercapai.")
    else:
        st.error("❌ Target kehadiran tidak tercapai.")
    catatan_rizal = st.text_area("Catatan Rizal", height=200, value=catatan_default_rizal, key="catatan_rizal")

    if st.button("💾 Simpan Rizal"):
        simpan_kehadiran("Rizal", kehadiran_rizal, catatan_rizal)
        st.success("✅ Data Rizal disimpan.")

# Tab Thesi
with tab2:
    default_thesi, catatan_default_thesi = load_kehadiran("Thesi")
    kehadiran_thesi, hari_kerja_thesi, hadir_sampai_hari_ini_thesi = tampilkan_kalender("Thesi", default_thesi)
    hadir_thesi = sum(1 for v in kehadiran_thesi.values() if v is True)
    min_hadir = math.ceil(hari_kerja_thesi * 0.7)
    maks_bolos = hari_kerja_thesi - min_hadir
    bolos_thesi = hari_kerja_thesi - hadir_thesi

    # st.write(f"Hadir: **{hadir_thesi}**")
    st.info(f"📅 Jumlah hadir hingga hari ini: **{hadir_sampai_hari_ini_thesi} hari**")
    st.write(f"Total hari kerja: **{hari_kerja_thesi}**")
    st.write(f"Maks bolos: **{maks_bolos}**")
    
    fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=bolos_thesi,
    domain={'x': [0, 1], 'y': [0, 1]},
    gauge={
        'axis': {'range': [0, hari_kerja_thesi]},
        'bar': {'color': "red"},
        'steps': [
            {'range': [0, maks_bolos], 'color': "lightgreen"},
            {'range': [maks_bolos, hari_kerja_thesi], 'color': "lightcoral"},
        ],
    },
    title={'text': "Jumlah Bolos"}
    ))
    fig.update_layout(height=350, margin=dict(t=50, b=20))
    st.plotly_chart(fig, use_container_width=True, key="thesi_gauge")


    if hadir_thesi >= min_hadir:
        st.success("✅ Target kehadiran tercapai.")
    else:
        st.error("❌ Target kehadiran tidak tercapai.")
    catatan_thesi = st.text_area("Catatan Thesi", height=200, value=catatan_default_thesi, key="catatan_thesi")

    if st.button("💾 Simpan Thesi"):
        simpan_kehadiran("Thesi", kehadiran_thesi, catatan_thesi)
        st.success("✅ Data Thesi disimpan.")

# Tab Rekap Bersamaan
with tab3:
    st.markdown("### Jumlah Hari Masuk Bersamaan (hingga hari ini)")
    today = datetime.today().date()
    hari_bersamaan = 0
    total_hari_kerja = 0

    for d in date_list:
        if d.date() > today:
            continue
        is_red = f"{d.day:02d}-{d.month:02d}" in tanggal_merah
        is_sunday = d.weekday() == 6
        if not is_red and not is_sunday:
            total_hari_kerja += 1
            rizal_hadir = kehadiran_rizal.get(d) is True
            thesi_hadir = kehadiran_thesi.get(d) is True
            if rizal_hadir and thesi_hadir:
                hari_bersamaan += 1

    st.metric("Total Hari Kerja (sampai hari ini)", total_hari_kerja)
    st.metric("Hari Masuk Bersamaan", hari_bersamaan)
    uang_bensin = hari_bersamaan * 2500
    st.metric("Uang Bensin (sementara)", f"Rp {uang_bensin:,.0f}".replace(",", "."))


