import streamlit as st
import calendar
from datetime import datetime, date, timedelta
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
st.set_page_config(page_title="Kalender Kehadiran", layout="wide")
st.title("📅 Kalender Kehadiran")

# --------------------------
# Input bulan & tahun
# --------------------------
today = date.today()
tahun = st.sidebar.number_input("Tahun", min_value=2000, max_value=2100, value=today.year)
bulan = st.sidebar.number_input("Bulan", min_value=1, max_value=12, value=today.month)

# --------------------------
# Daftar tanggal merah (manual contoh)
# --------------------------
tanggal_merah = [
    "01-01", "17-08", "25-12"  # contoh: Tahun Baru, Kemerdekaan, Natal
]

# --------------------------
# Generate minggu dalam bulan
# --------------------------
cal = calendar.Calendar(firstweekday=0)  # 0 = Senin
weeks = cal.monthdatescalendar(tahun, bulan)

# --------------------------
# Load data dari DB
# --------------------------
def load_data(nama):
    doc = coll.find_one({"nama": nama, "tahun": tahun, "bulan": bulan})
    if doc:
        return [datetime.strptime(d, "%Y-%m-%d").date() for d in doc["tanggal"]]
    return []

# --------------------------
# Save data ke DB
# --------------------------
def save_data(nama, date_list):
    coll.update_one(
        {"nama": nama, "tahun": tahun, "bulan": bulan},
        {"$set": {"tanggal": [d.isoformat() for d in date_list]}},
        upsert=True
    )

# --------------------------
# Tampilkan kalender autosave
# --------------------------
def tampilkan_kalender_autosave(label_user, date_list):
    today = date.today()  # ✅ fix NameError

    for week_idx, week in enumerate(weeks):
        cols = st.columns(7)
        for i, d in enumerate(week):
            with cols[i]:
                if d.month == bulan and d.year == tahun:
                    label = f"{d.day}"
                    default_val = d in date_list

                    # ✅ fix duplicate key
                    key = f"{label_user}_{d.isoformat()}_{week_idx}_{i}"

                    new_val = st.checkbox(label, key=key, value=default_val)

                    if new_val != default_val:
                        if new_val and d not in date_list:
                            date_list.append(d)
                        elif not new_val and d in date_list:
                            date_list.remove(d)
                        save_data(label_user, date_list)  # auto-save

    # hitung hari kerja
    hari_kerja_sampai_hari_ini = sum(
        1 for d in date_list
        if d <= today and d.weekday() < 6 and f"{d.day:02d}-{d.month:02d}" not in tanggal_merah
    )

    hadir_sampai_hari_ini = sum(
        1 for d in date_list if d <= today and d.weekday() < 6
    )

    return date_list, hari_kerja_sampai_hari_ini, hadir_sampai_hari_ini

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["Jadwal Rizal", "Jadwal Thesi", "Rekap Bersamaan"])

# Tab Rizal
with tab1:
    date_list_rizal = load_data("Rizal")
    kehadiran_rizal, hari_kerja_rizal, hadir_sampai_hari_ini_rizal = tampilkan_kalender_autosave("Rizal", date_list_rizal)

    st.subheader("Statistik Rizal")
    st.write(f"Hari kerja sampai hari ini: {hari_kerja_rizal}")
    st.write(f"Hadir sampai hari ini: {hadir_sampai_hari_ini_rizal}")

# Tab Thesi
with tab2:
    date_list_thesi = load_data("Thesi")
    kehadiran_thesi, hari_kerja_thesi, hadir_sampai_hari_ini_thesi = tampilkan_kalender_autosave("Thesi", date_list_thesi)

    st.subheader("Statistik Thesi")
    st.write(f"Hari kerja sampai hari ini: {hari_kerja_thesi}")
    st.write(f"Hadir sampai hari ini: {hadir_sampai_hari_ini_thesi}")

# Tab Rekap Bersamaan
with tab3:
    st.subheader("📊 Rekap Bersamaan")

    total_rizal = len(kehadiran_rizal)
    total_thesi = len(kehadiran_thesi)

    st.write(f"Total kehadiran Rizal: {total_rizal}")
    st.write(f"Total kehadiran Thesi: {total_thesi}")

    sama2_hadir = len(set(kehadiran_rizal) & set(kehadiran_thesi))
    st.write(f"Sama-sama hadir: {sama2_hadir}")
