import streamlit as st
import calendar
from datetime import datetime, timedelta

st.title('Kalender Khusus (16 - 15)')

st.sidebar.header("Pilih Rentang Tanggal")

# Input tahun dan bulan awal (misal: Januari)
year = st.sidebar.number_input("Pilih Tahun", min_value=1900, max_value=3000, value=datetime.now().year)
month = st.sidebar.selectbox('Pilih Bulan Awal', list(calendar.month_name)[1:], index=datetime.now().month - 1)
month_number = list(calendar.month_name).index(month)

# Tentukan tanggal awal dan akhir
start_date = datetime(year, month_number, 16)
# Akhir adalah tanggal 15 bulan berikutnya
if month_number == 12:
    end_date = datetime(year + 1, 1, 15)
else:
    end_date = datetime(year, month_number + 1, 15)

# Buat daftar tanggal dari 16 hingga 15
date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

st.subheader(f"Kalender dari {start_date.strftime('%d %B %Y')} hingga {end_date.strftime('%d %B %Y')}")

# Inisialisasi dictionary untuk status
status_dict = {}
for date in date_range:
    date_str = date.strftime('%d %b %Y (%A)')
    status = st.selectbox(f"{date_str}", ['Masuk', 'Tidak Masuk'], key=date_str)
    status_dict[date_str] = status

# Tampilkan hasil
st.markdown("## Rekap Kehadiran")
for date_str, status in status_dict.items():
    st.write(f"{date_str}: {status}")
