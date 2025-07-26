import streamlit as st
import calendar
from datetime import datetime, timedelta
import plotly.graph_objects as go
import math

st.set_page_config(layout="wide")

# Sidebar Input Periode
st.sidebar.header("Pilih Bulan Awal")
year = st.sidebar.number_input("Tahun", min_value=1900, max_value=2100, value=datetime.now().year)
month = st.sidebar.selectbox("Bulan", list(calendar.month_name)[1:], index=datetime.now().month - 1)
month_number = list(calendar.month_name).index(month)

# Tanggal Awal dan Akhir (16 - 15 bulan depan)
start_date = datetime(year, month_number, 16)
end_date = datetime(year + 1, 1, 15) if month_number == 12 else datetime(year, month_number + 1, 15)

# Buat daftar tanggal
date_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

# Hardcoded tanggal merah (bisa pakai API kalau mau otomatis)
tanggal_merah = [
    "01-01", "17-08", "25-12", "10-04", "11-04", "12-04"  # Contoh
]
tanggal_merah_set = set(tanggal_merah)

# Fungsi bantu untuk menampilkan kalender per user
def tampilkan_kalender(label_user):
    st.markdown(f"### Kehadiran {label_user}")
    days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

    # Buat struktur minggu
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

    # Header hari
    cols = st.columns(7)
    for i, d in enumerate(days):
        with cols[i]:
            st.markdown(f"**{d}**")

    hadir_dict = {}
    total_hari_kerja = 0

    # Tampilkan per minggu
    for week in weeks:
        cols = st.columns(7)
        for i, date in enumerate(week):
            with cols[i]:
                if date != "":
                    label = date.strftime("%d %b")
                    key = f"{label_user}_{date.strftime('%Y-%m-%d')}"
                    is_red = f"{date.day:02d}-{date.month:02d}" in tanggal_merah_set
                    is_sunday = date.weekday() == 6
                    if is_red or is_sunday:
                        st.markdown(f"<div style='color:red'>{label}<br><em>Libur</em></div>", unsafe_allow_html=True)
                        hadir_dict[date] = None
                    else:
                        total_hari_kerja += 1
                        hadir_dict[date] = st.checkbox(label, key=key)
                else:
                    st.markdown(" ")

    return hadir_dict, total_hari_kerja

# ======== Tabs ========
tab1, tab2, tab3 = st.tabs(["Jadwal Rizal", "Jadwal Thesi", "Rekap Bersamaan"])

with tab1:
    kehadiran_rizal, hari_kerja_rizal = tampilkan_kalender("Rizal")
    hadir_rizal = sum(1 for val in kehadiran_rizal.values() if val is True)
    st.write(f"Total hari kerja: **{hari_kerja_rizal}**")
    st.write(f"Jumlah hadir: **{hadir_rizal}**")

    min_hadir = math.floor(hari_kerja_rizal * 0.7)
    maks_bolos = hari_kerja_rizal - min_hadir
    st.write(f"Minimal kehadiran (70%): **{min_hadir}**")

    if hadir_rizal >= min_hadir:
        st.success("✅ Target kehadiran tercapai.")
    else:
        st.error("❌ Target kehadiran tidak tercapai.")

with tab2:
    kehadiran_thesi, hari_kerja_thesi = tampilkan_kalender("Thesi")
    hadir_thesi = sum(1 for val in kehadiran_thesi.values() if val is True)
    st.write(f"Total hari kerja: **{hari_kerja_thesi}**")
    st.write(f"Jumlah hadir: **{hadir_thesi}**")

    min_hadir = math.floor(hari_kerja_thesi * 0.7)
    maks_bolos = hari_kerja_thesi - min_hadir
    st.write(f"Minimal kehadiran (70%): **{min_hadir}**")

    if hadir_thesi >= min_hadir:
        st.success("✅ Target kehadiran tercapai.")
    else:
        st.error("❌ Target kehadiran tidak tercapai.")

with tab3:
    st.markdown("### Jumlah Hari Masuk Bersamaan")

    hari_bersamaan = 0
    total_hari_kerja = 0
    for d in date_list:
        is_red = f"{d.day:02d}-{d.month:02d}" in tanggal_merah_set
        is_sunday = d.weekday() == 6
        if not is_red and not is_sunday:
            total_hari_kerja += 1
            rizal_hadir = kehadiran_rizal.get(d) is True
            thesi_hadir = kehadiran_thesi.get(d) is True
            if rizal_hadir and thesi_hadir:
                hari_bersamaan += 1

    st.metric("Total Hari Kerja", total_hari_kerja)
    st.metric("Jumlah Hari Masuk Bersamaan", hari_bersamaan)

    # Gauge chart pakai plotly
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=hari_bersamaan,
        gauge={
            'axis': {'range': [0, total_hari_kerja]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, total_hari_kerja * 0.5], 'color': "lightcoral"},
                {'range': [total_hari_kerja * 0.5, total_hari_kerja], 'color': "lightgreen"},
            ],
        },
        title={'text': "Hari Masuk Bersamaan"}
    ))
    st.plotly_chart(fig, use_container_width=True)
