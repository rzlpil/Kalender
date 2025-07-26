import streamlit as st
import calendar
from datetime import datetime, timedelta

# Set halaman
st.set_page_config(layout="wide")
st.title("Kalender Kehadiran (16 - 15)")

# Input
st.sidebar.header("Pilih Bulan Awal")
year = st.sidebar.number_input("Tahun", min_value=1900, max_value=2100, value=datetime.now().year)
month = st.sidebar.selectbox("Bulan", list(calendar.month_name)[1:], index=datetime.now().month - 1)
month_number = list(calendar.month_name).index(month)

# Tentukan range tanggal
start_date = datetime(year, month_number, 16)
if month_number == 12:
    end_date = datetime(year + 1, 1, 15)
else:
    end_date = datetime(year, month_number + 1, 15)

# List tanggal dari 16 hingga 15 bulan depan
date_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

# Daftar tanggal merah (contoh sederhana – bisa pakai API)
tanggal_merah = [
    "01-01", "17-08", "25-12",  # Tahun Baru, Kemerdekaan, Natal
    "10-04", "11-04", "12-04",  # Idul Fitri contoh
]
tanggal_merah_full = [f"{dt.day:02d}-{dt.month:02d}" for dt in date_list if f"{dt.day:02d}-{dt.month:02d}" in tanggal_merah]

# Tampilkan sebagai grid kalender
st.subheader(f"Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}")
days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

# Buat struktur kalender mingguan
weeks = []
week = [""] * 7
for date in date_list:
    day_idx = date.weekday()  # 0 = Monday ... 6 = Sunday
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

# Kalender mingguan
for week in weeks:
    cols = st.columns(7)
    for i, date in enumerate(week):
        with cols[i]:
            if date != "":
                label = date.strftime("%d %b")
                key = date.strftime("%Y-%m-%d")
                tag_merah = f"{date.day:02d}-{date.month:02d}" in tanggal_merah
                is_sunday = date.weekday() == 6

                if tag_merah or is_sunday:
                    st.markdown(f"<div style='color:red'>{label}<br><em>Libur</em></div>", unsafe_allow_html=True)
                else:
                    checked = st.checkbox(label, key=key)
            else:
                st.markdown(" ")

# Rekap
st.markdown("### Rekap Kehadiran")
for date in date_list:
    key = date.strftime("%Y-%m-%d")
    tag_merah = f"{date.day:02d}-{date.month:02d}" in tanggal_merah
    is_sunday = date.weekday() == 6
    if not (tag_merah or is_sunday):
        if st.session_state.get(key):
            st.write(f"{date.strftime('%d %B %Y (%A)')}: ✅ Masuk")
