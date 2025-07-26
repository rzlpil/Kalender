import streamlit as st
import calendar
from datetime import datetime, timedelta
import plotly.graph_objects as go
import math

# Atur halaman
st.set_page_config(layout="wide")
st.title("Kalender Kehadiran (16 - 15) + Evaluasi 70%")

# Sidebar input
st.sidebar.header("Pilih Bulan Awal")
year = st.sidebar.number_input("Tahun", min_value=1900, max_value=2100, value=datetime.now().year)
month = st.sidebar.selectbox("Bulan", list(calendar.month_name)[1:], index=datetime.now().month - 1)
month_number = list(calendar.month_name).index(month)

# Tanggal rentang
start_date = datetime(year, month_number, 16)
if month_number == 12:
    end_date = datetime(year + 1, 1, 15)
else:
    end_date = datetime(year, month_number + 1, 15)

date_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

# Tanggal merah (hardcoded contoh)
tanggal_merah = [
    "01-01", "17-08", "25-12",  # Tahun Baru, Kemerdekaan, Natal
    "10-04", "11-04", "12-04",  # Idul Fitri
]
tanggal_merah_full = [f"{dt.day:02d}-{dt.month:02d}" for dt in date_list if f"{dt.day:02d}-{dt.month:02d}" in tanggal_merah]

# Header kalender
st.subheader(f"Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}")
days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

# Bangun kalender mingguan
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

# Checkbox untuk hari kerja
hadir_dict = {}
total_hari_kerja = 0
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
                    hadir_dict[key] = None
                else:
                    total_hari_kerja += 1
                    checked = st.checkbox(label, key=key)
                    hadir_dict[key] = checked
            else:
                st.markdown(" ")

# Hitung kehadiran
jumlah_hadir = sum([1 for v in hadir_dict.values() if v is True])
jumlah_tidak_hadir = total_hari_kerja - jumlah_hadir
minimal_hadir = math.ceil(int(total_hari_kerja * 0.7))
maks_tidak_hadir = total_hari_kerja - minimal_hadir

# Tampilkan rekap
st.markdown("### Rekap Kehadiran")
st.write(f"Total Hari Kerja: **{total_hari_kerja}**")
st.write(f"Jumlah Hari Hadir: **{jumlah_hadir}**")
st.write(f"Jumlah Hari Tidak Hadir: **{jumlah_tidak_hadir}**")
st.write(f"Minimal Kehadiran (70%): **{minimal_hadir} hari**")
st.write(f"Maksimal TIdak Hadir (30%): **{maks_tidak_hadir} hari**")

if jumlah_hadir >= minimal_hadir:
    st.success("✅ Target kehadiran tercapai!")
else:
    st.error("❌ Target kehadiran **tidak tercapai**.")

# Gauge chart
fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=jumlah_tidak_hadir,
    delta={'reference': maks_tidak_hadir, 'increasing': {'color': "red"}},
    gauge={
        'axis': {'range': [0, total_hari_kerja]},
        'bar': {'color': "orange"},
        'steps': [
            {'range': [0, maks_tidak_hadir], 'color': "lightgreen"},
            {'range': [maks_tidak_hadir, total_hari_kerja], 'color': "lightcoral"},
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': maks_tidak_hadir
        }
    },
    title={'text': "Ketidakhadiran vs Batas Maksimal"}
))

st.plotly_chart(fig, use_container_width=True)
