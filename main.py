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

# ===== Range Absen (date objects) =====
start_absen = date(pm_year, pm_month, 11)
end_absen = date(year, month_number, 10)
date_list = [start_absen + timedelta(days=i) for i in range((end_absen - start_absen).days + 1)]

# ===== Range Rekap Bensin (date objects) =====
start_rekap = date(pm_year, pm_month, 17)
end_rekap = date(year, month_number, 16)
# rekap_date_list not strictly necessary but kept for potential use
rekap_date_list = [start_rekap + timedelta(days=i) for i in range((end_rekap - start_rekap).days + 1)]

# Tanggal merah (libur nasional) format DD-MM
tanggal_merah = {"01-01", "17-08", "25-12", "10-04", "11-04", "12-04"}

# --------------------------
# Load dari MongoDB
# --------------------------
def load_kehadiran(user):
    """
    Return:
      kehadiran: dict with keys = datetime.date, values = bool (True/False) or None for libur
      catatan: string
    """
    kehadiran = {}
    for doc in coll.find({"user": user, "type": {"$ne": "catatan"}}):
        # dokumen menyimpan tanggal sebagai 'YYYY-MM-DD'
        try:
            d = datetime.strptime(doc["tanggal"], '%Y-%m-%d').date()
        except Exception:
            # jika format beda, skip
            continue
        kehadiran[d] = doc.get("hadir", False)
    catatan_doc = coll.find_one({"user": user, "type": "catatan"})
    catatan = catatan_doc["catatan"] if catatan_doc else ""
    return kehadiran, catatan

# --------------------------
# Simpan ke MongoDB
# --------------------------
def simpan_kehadiran(user, kehadiran, catatan):
    """
    kehadiran: dict(date -> bool/None)
    """
    records = []
    for tanggal, hadir in kehadiran.items():
        if tanggal:
            records.append({
                "user": user,
                "tanggal": tanggal.strftime('%Y-%m-%d'),
                "hadir": bool(hadir) if hadir is not None else None
            })
    # hapus semua record lama untuk user (kecuali 'catatan'), lalu insert baru
    coll.delete_many({"user": user, "type": {"$ne": "catatan"}})
    if records:
        coll.insert_many(records)
    # simpan catatan
    coll.update_one(
        {"user": user, "type": "catatan"},
        {"$set": {"catatan": catatan, "type": "catatan"}},
        upsert=True
    )

# --------------------------
# Fungsi Kalender (pakai date_list)
# --------------------------
def tampilkan_kalender(label_user, default_kehadiran):
    st.markdown(f"### Kehadiran {label_user}")
    days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

    today = date.today()
    hadir_dict = {}
    total_hari_kerja = 0
    hadir_sampai_hari_ini = 0

    # Susun minggu (list of weeks, each week is length 7, elements either date or "")
    weeks = []
    week = []
    # Start week with blanks until the first date's weekday
    first_weekday = date_list[0].weekday()  # 0=Mon ... 6=Sun
    week = [""] * first_weekday

    for d in date_list:
        week.append(d)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        # pad the last week
        while len(week) < 7:
            week.append("")
        weeks.append(week)

    # header
    cols = st.columns(7)
    for i, dow in enumerate(days):
        with cols[i]:
            st.markdown(f"**{dow}**")

    # kalender
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
                    default = default_kehadiran.get(d, True)
                    hadir = st.checkbox(label, key=key, value=default)
                    hadir_dict[d] = hadir
                    if d <= today and hadir:
                        hadir_sampai_hari_ini += 1

    return hadir_dict, total_hari_kerja, hadir_sampai_hari_ini

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["Jadwal Rizal", "Jadwal Thesi", "Rekap Bersamaan"])

# Tab Rizal
with tab1:
    default_rizal, catatan_default_rizal = load_kehadiran("Rizal")
    kehadiran_rizal, hari_kerja_rizal, hadir_sampai_hari_ini_rizal = tampilkan_kalender("Rizal", default_rizal)
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
    st.markdown("### Rekap Hari Masuk Bersamaan per Periode (17→16)")
    today = date.today()
    periode_awal = start_rekap  # already date
    hasil_rekap = []

    # Pastikan default kehadiran sudah di-load supaya kehadiran_rizal/thesi tersedia
    default_rizal, _ = load_kehadiran("Rizal")
    default_thesi, _ = load_kehadiran("Thesi")
    kehadiran_rizal = default_rizal
    kehadiran_thesi = default_thesi

    # Loop periode 17..16 per bulan sampai hari ini
    while periode_awal <= today:
        # periode akhir = tanggal 16 bulan berikutnya
        if periode_awal.month == 12:
            periode_akhir = date(periode_awal.year + 1, 1, 16)
        else:
            periode_akhir = date(periode_awal.year, periode_awal.month + 1, 16)

        # jika periode akhir melewati hari ini, pangkas
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
                rizal_hadir = kehadiran_rizal.get(cek_tanggal) is True
                thesi_hadir = kehadiran_thesi.get(cek_tanggal) is True
                if rizal_hadir and thesi_hadir:
                    hari_bersamaan += 1
            cek_tanggal += timedelta(days=1)

        hasil_rekap.append({
            "Periode": f"{periode_awal.strftime('%d %b %Y')} - {periode_akhir.strftime('%d %b %Y')}",
            "Hari Kerja": total_hari_kerja,
            "Masuk Bersamaan": hari_bersamaan,
            "Uang Bensin": hari_bersamaan * 2500
        })

        # geser ke periode berikutnya (mulai 17 bulan berikutnya)
        if periode_awal.month == 12:
            periode_awal = date(periode_awal.year + 1, 1, 17)
        else:
            periode_awal = date(periode_awal.year, periode_awal.month + 1, 17)

    st.table(hasil_rekap)

    # --------------------------
    # Tambahan: filter tanggal custom oleh user
    # --------------------------
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
        # hitung total hari kerja (exclude libur & minggu) dan hari bersamaan di rentang ini
        total_hari_kerja_manual = 0
        hari_bersamaan_manual = 0
        cek_t = manual_start
        while cek_t <= manual_end:
            is_red = f"{cek_t.day:02d}-{cek_t.month:02d}" in tanggal_merah
            is_sunday = cek_t.weekday() == 6
            if not is_red and not is_sunday:
                total_hari_kerja_manual += 1
                rizal_hadir = kehadiran_rizal.get(cek_t) is True
                thesi_hadir = kehadiran_thesi.get(cek_t) is True
                if rizal_hadir and thesi_hadir:
                    hari_bersamaan_manual += 1
            cek_t += timedelta(days=1)

        uang_bensin_manual = hari_bersamaan_manual * 2500

        st.metric("Total Hari Kerja (rentang)", total_hari_kerja_manual)
        st.metric("Hari Masuk Bersamaan", hari_bersamaan_manual)
        st.metric("Uang Bensin (Rp)", f"Rp {uang_bensin_manual:,.0f}".replace(",", "."))
