import streamlit as st
import calendar
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(layout="wide")
st.title("Kalender Masuk / Tidak Masuk (16 - 15)")

# Sidebar input
st.sidebar.header("Pilih Bulan Awal")
year = st.sidebar.number_input("Tahun", min_value=1900, max_value=2100, value=datetime.now().year)
month = st.sidebar.selectbox("Bulan", list(calendar.month_name)[1:], index=datetime.now().month - 1)
month_number = list(calendar.month_name).index(month)

# Hitung tanggal mulai dan selesai (16 - 15 bulan berikutnya)
start_date = datetime(year, month_number, 16)
if month_number == 12:
    end_date = datetime(year + 1, 1, 15)
else:
    end_date = datetime(year, month_number + 1, 15)

# Buat list tanggal
date_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

# Susun kalender per minggu (7 hari) mulai dari hari Senin
st.subheader(f"Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}")
days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

# Buat struktur kalender
weeks = []
week = ["" for _ in range(7)]
for date in date_list:
    day_index = (date.weekday())  # Monday = 0
    if date == date_list[0]:  # Tanggal pertama
        week = [""] * day_index
    week.append(date)
    if len(week) == 7:
        weeks.append(week)
        week = []
if week:
    while len(week) < 7:
        week.append("")
    weeks.append(week)

# Tampilkan grid
st.markdown("### Kalender:")
for week in weeks:
    cols = st.columns(7)
    for i, date in enumerate(week):
        with cols[i]:
            if date != "":
                label = date.strftime("%d %b")
                checked = st.checkbox(label, key=str(date))
            else:
                st.markdown(" ")

# ✨ Rekap setelah checkbox
st.markdown("### Rekap Masuk:")
for date in date_list:
    if st.session_state.get(str(date)):
        st.write(f"{date.strftime('%d %B %Y (%A)')}: ✅ Masuk")
