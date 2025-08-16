import streamlit as st
import calendar
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import math
from pymongo import MongoClient

# --------------------------
# Config MongoDB
# --------------------------
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["kalender_db"]
coll = db["kehadiran"]

# --------------------------
# Page setup
# --------------------------
st.set_page_config(layout="wide")

# Sidebar Pilih Periode
st.sidebar.header("Pilih Bulan Awal")
year = st.sidebar.number_input("Tahun", min_value=1900, max_value=2100, value=datetime.now().year)
month = st.sidebar.selectbox("Bulan", list(calendar.month_name)[1:], index=datetime.now().month - 1)
month_number = list(calendar.month_name).index(month)

# --------------------------
# Helper: previous month/year
# --------------------------
def prev_month_year(y, m):
    if m == 1:
        return y - 1, 12
    else:
        return y, m - 1

pm_year, pm_month = prev_month_year(year, month_number)

# --------------------------
# Range Absen Rizal (13 -> 12)
# --------------------------
start_absen_rizal = date(pm_year, pm_month, 13)
end_absen_rizal = date(year, month_number, 12)
date_list_rizal = [start_absen_rizal + timedelta(days=i)
                   for i in range((end_absen_rizal - start_absen_rizal).days + 1)]

# --------------------------
# Range Absen Thesi (11 -> 10)
# --------------------------
start_absen_thesi = date(pm_year, pm_month, 11)
end_absen_thesi = date(year, month_number, 10)
date_list_thesi = [start_absen_thesi + timedelta(days=i)
                   for i in range((end_absen_thesi - start_absen_thesi).days + 1)]

# --------------------------
# Range Rekap Bensin (17 -> 16)
# --------------------------
start_rekap = date(pm_year, pm_month, 17)
end_rekap = date(year, month_number, 16)
rekap_date_list = [start_rekap + timedelta(days=i)
                   for i in range((end_rekap - start_rekap).days + 1)]

# --------------------------
# Tanggal merah (libur nasional)
# --------------------------
tanggal_merah = {"01-01", "17-08", "25-12", "10-04", "11-04", "12-04"}

# --------------------------
# Load dari MongoDB
# --------------------------
def load_kehadiran(user):
    kehadiran = {}
    for doc in coll.find({"user": user, "type": {"$ne": "catatan"}}):
        try:
            d = datetime.strptime(doc["tanggal"], '%Y-%m-%d').date()
        except Exception:
            continue
        kehadiran[d] = doc.get("hadir", False)
    catatan_doc = coll.find_one({"user": user, "type": "catatan"})
    catatan = catatan_doc["catatan"] if catatan_doc else ""
    return kehadiran, catatan

# --------------------------
# Simpan ke MongoDB
# --------------------------
def simpan_kehadiran(user, kehadiran, catatan):
    records = []
    for tanggal, hadir in kehadiran.items():
        if tanggal:
            records.append({
                "user": user,
                "tanggal": tanggal.strftime('%Y-%m-%d'),
                "hadir": bool(hadir) if hadir is not None else None
            })
    coll.delete_many({"user": user, "type": {"$ne": "catatan"}})
    if records:
        coll.insert_many(records)
    coll.update_one(
        {"user": user, "type": "catatan"},
        {"$set": {"catatan": catatan, "type": "catatan"}},
        upsert=True
    )

# --------------------------
# Fungsi Kalender Auto-save
# --------------------------
def tampilkan_kalender_autosave(label_user, date_list):
    st.markdown(f"### Kehadiran {label_user}")

    # Load dari session_state atau MongoDB
    if f"kehadiran_{label_user}" not in st.session_state:
        default_kehadiran, catatan = load_kehadiran(label_user)
        st.session_state[f"kehadiran_{label_user}"] = default_kehadiran
        st.session_state[f"catatan_{label_user}"] = catatan

    hadir_dict = st.session_state[f"kehadiran_{label_user}"]
    days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    today = date.today()
    total_hari_kerja = 0
    hadir_sampai_hari_ini = 0

    # Susun minggu
    weeks = []
    week = [""] * date_list[0].weekday()
    for d in date_list:
        week.append(d)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append("")
        weeks.append(week)

    # Header
    cols = st.columns(7)
    for i, dow in enumerate(days):
        with cols[i]:
            st.markdown(f"**{dow}**")

    # Isi kalender
    for week in weeks:
        cols = st.columns(7)
        for i, d in enumerate(week):
            with cols[i]:
                if d == "":
                    st.markdown(" ")
                    continue
                label = d.strftime("%d %b")
                key = f"{label_user}_{d.isoformat()}"
                is_red = f"{d.day:02d}-{d.month:02d}" in tanggal_merah
                is_sunday = d.weekday() == 6
                if is_red or is_sunday:
                    st.markdown(f"<div style='color:red'>{label}<br><em>Libur</em></div>", unsafe_allow_html=True)
                    hadir_dict[d] = None
                else:
                    total_hari_kerja += 1
                    default_val = hadir_dict.get(d, True)

                    # Checkbox auto-save
                    new_val = st.checkbox(label, key=key, value=default_val)
                    if new_val != hadir_dict.get(d):
                        hadir_dict[d] = new_val
                        simpan_kehadiran(label_user, hadir_dict, st.session_state[f"catatan_{label_user}"])

                    if d <= today and hadir_dict[d]:
                        hadir_sampai_hari_ini += 1

    return hadir_dict, total_hari_kerja, hadir_sampai_hari_ini

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["Jadwal Rizal", "Jadwal Thesi", "Rekap Bersamaan"])

# Tab Rizal
with tab1:
    kehadiran_rizal, hari_kerja_rizal, hadir_sampai_hari_ini_rizal = tampilkan_kalender_autosave("Rizal", date_list_rizal)
    hadir_rizal = sum(1 for v in kehadiran_rizal.values() if v is True)
    min_hadir = math.ceil(hari_kerja_rizal * 0.7)
    maks_bolos = hari_kerja_rizal - min_hadir
    bolos_rizal = hari_kerja_rizal - hadir_rizal

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
    st.plotly_chart(fig, use_container_width=True)

    if hadir_rizal >= min_hadir:
        st.success("✅ Target kehadiran tercapai.")
    else:
        st.error("❌ Target kehadiran tidak tercapai.")

    # Catatan dengan auto-save
    catatan_rizal = st.text_area("Catatan Rizal", height=200, value=st.session_state["catatan_Rizal"])
    if catatan_rizal != st.session_state["catatan_Rizal"]:
        st.session_state["catatan_Rizal"] = catatan_rizal
        simpan_kehadiran("Rizal", kehadiran_rizal, catatan_rizal)

# Tab Thesi
with tab2:
    kehadiran_thesi, hari_kerja_thesi, hadir_sampai_hari_ini_thesi = tampilkan_kalender_autosave("Thesi", date_list_thesi)
    hadir_thesi = sum(1 for v in kehadiran_thesi.values() if v is True)
    min_hadir = math.ceil(hari_kerja_thesi * 0.7)
    maks_bolos = hari_kerja_thesi - min_hadir
    bolos_thesi = hari_kerja_thesi - hadir_thesi

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
    st.plotly_chart(fig, use_container_width=True)

    if hadir_thesi >= min_hadir:
        st.success("✅ Target kehadiran tercapai.")
    else:
        st.error("❌ Target kehadiran tidak tercapai.")

    # Catatan auto-save
    catatan_thesi = st.text_area("Catatan Thesi", height=200, value=st.session_state["catatan_Thesi"])
    if catatan_thesi != st.session_state["catatan_Thesi"]:
        st.session_state["catatan_Thesi"] = catatan_thesi
        simpan_kehadiran("Thesi", kehadiran_thesi, catatan_thesi)

# Tab Rekap Bersamaan
with tab3:
    st.markdown("### Rekap Hari Masuk Bersamaan per Periode (17→16)")
    today = date.today()
    periode_awal = start_rekap
    hasil_rekap = []

    kehadiran_rizal, _ = load_kehadiran("Rizal")
    kehadiran_thesi, _ = load_kehadiran("Thesi")

    while periode_awal <= today:
        if periode_awal.month == 12:
            periode_akhir = date(periode_awal.year + 1, 1, 16)
        else:
            periode_akhir = date(periode_awal.year, periode_awal.month + 1, 16)

        if periode_akhir > today:
            periode_akhir = today

        total_hari_kerja = 0
        hari_bersamaan = 0

        cek_tanggal = periode_awal
        while cek_tanggal <= periode_akhir:
            is_red = f"{cek_tanggal.day:02d}-{cek_tanggal.month:02d}" in tanggal_merah
            is_sunday = cek_tanggal.weekday() == 6
            if not is_red and not is_sunday:
                total_hari_kerja += 1
                if kehadiran_rizal.get(cek_tanggal) and kehadiran_thesi.get(cek_tanggal):
                    hari_bersamaan += 1
            cek_tanggal += timedelta(days=1)

        hasil_rekap.append({
            "Periode": f"{periode_awal.strftime('%d %b %Y')} - {periode_akhir.strftime('%d %b %Y')}",
            "Hari Kerja": total_hari_kerja,
            "Masuk Bersamaan": hari_bersamaan,
            "Uang Bensin": hari_bersamaan * 2500
        })

        if periode_awal.month == 12:
            periode_awal = date(periode_awal.year + 1, 1, 17)
        else:
            periode_awal = date(periode_awal.year, periode_awal.month + 1, 17)

    st.table(hasil_rekap)

    # Rekap manual
    st.markdown("----")
    st.markdown("### Rekap Manual (Pilih rentang tanggal sendiri)")
    col1, col2 = st.columns(2)
    with col1:
        manual_start = st.date_input("Tanggal Awal", value=start_rekap)
    with col2:
        manual_end = st.date_input("Tanggal Akhir", value=today)

    if manual_end < manual_start:
        st.error("Tanggal akhir tidak boleh sebelum tanggal awal.")
    else:
        total_hari_kerja_manual = 0
        hari_bersamaan_manual = 0
        cek_t = manual_start
        while cek_t <= manual_end:
            is_red = f"{cek_t.day:02d}-{cek_t.month:02d}" in tanggal_merah
            is_sunday = cek_t.weekday() == 6
            if not is_red and not is_sunday:
                total_hari_kerja_manual += 1
                if kehadiran_rizal.get(cek_t) and kehadiran_thesi.get(cek_t):
                    hari_bersamaan_manual += 1
            cek_t += timedelta(days=1)

        st.metric("Total Hari Kerja (rentang)", total_hari_kerja_manual)
        st.metric("Hari Masuk Bersamaan", hari_bersamaan_manual)
        st.metric("Uang Bensin (Rp)", f"Rp {hari_bersamaan_manual * 2500:,.0f}".replace(",", "."))
