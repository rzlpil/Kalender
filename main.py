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

# --------------------------
# Util
# --------------------------
def get_date_list(year, month):
    c = calendar.Calendar(firstweekday=0)
    return list(c.itermonthdates(year, month))

def load_data(label_user, date_list):
    doc = coll.find_one({"user": label_user})
    if doc:
        return doc.get("data", {}), doc.get("notes", "")
    else:
        return {}, ""

def save_data(label_user, data, notes):
    coll.update_one(
        {"user": label_user},
        {"$set": {"data": data, "notes": notes}},
        upsert=True,
    )

# --------------------------
# Kalender dengan autosave
# --------------------------
def tampilkan_kalender_autosave(label_user, date_list):
    today = date.today()
    tahun, bulan = today.year, today.month

    st.subheader(f"Kalender Kehadiran {label_user} - {calendar.month_name[bulan]} {tahun}")

    # Load dari DB
    data, notes = load_data(label_user, date_list)

    # Tanggal merah manual
    tanggal_merah = {
        "01-01", "08-03", "17-08", "25-12"
    }

    # Bikin grid kalender
    weeks = []
    week = []
    for d in date_list:
        if d.month == bulan:
            week.append(d)
            if len(week) == 7:
                weeks.append(week)
                week = []
    if week:
        weeks.append(week)

    # Render minggu per minggu
    for week_idx, week in enumerate(weeks):
        cols = st.columns(7)
        for i, d in enumerate(week):
            with cols[i]:
                label = f"{d.day:02d}"
                default_val = data.get(d.isoformat(), False)

                # Checkbox unik
                key = f"{label_user}_{d.isoformat()}_{week_idx}_{i}"
                new_val = st.checkbox(label, key=key, value=default_val)

                if new_val != default_val:
                    data[d.isoformat()] = new_val
                    save_data(label_user, data, notes)

    # Catatan user
    new_notes = st.text_area("Catatan", value=notes, key=f"catatan_{label_user}")
    if new_notes != notes:
        save_data(label_user, data, new_notes)

    # Statistik
    hari_kerja_sampai_hari_ini = sum(
        1 for d in date_list
        if d <= today and d.weekday() < 6 and f"{d.day:02d}-{d.month:02d}" not in tanggal_merah
    )
    hadir_sampai_hari_ini = sum(
        1 for d in date_list if d <= today and data.get(d.isoformat(), False)
    )

    st.write(f"Total hari kerja sampai hari ini: {hari_kerja_sampai_hari_ini}")
    st.write(f"Total hadir {label_user} sampai hari ini: {hadir_sampai_hari_ini}")

    return data, hari_kerja_sampai_hari_ini, hadir_sampai_hari_ini

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["Jadwal Rizal", "Jadwal Thesi", "Rekap Bersamaan"])

today = date.today()
tahun, bulan = today.year, today.month
date_list_rizal = get_date_list(tahun, bulan)
date_list_thesi = get_date_list(tahun, bulan)

# Tab Rizal
with tab1:
    kehadiran_rizal, hari_kerja_rizal, hadir_sampai_hari_ini_rizal = tampilkan_kalender_autosave("Rizal", date_list_rizal)

# Tab Thesi
with tab2:
    kehadiran_thesi, hari_kerja_thesi, hadir_sampai_hari_ini_thesi = tampilkan_kalender_autosave("Thesi", date_list_thesi)

# Tab Rekap
with tab3:
    st.subheader("Rekap Kehadiran Bersamaan")

    hadir_bersamaan = sum(
        1 for d in date_list_rizal
        if kehadiran_rizal.get(d.isoformat(), False) and kehadiran_thesi.get(d.isoformat(), False)
    )

    st.write(f"Hari kerja sampai hari ini: {hari_kerja_rizal}")
    st.write(f"Rizal hadir {hadir_sampai_hari_ini_rizal} hari")
    st.write(f"Thesi hadir {hadir_sampai_hari_ini_thesi} hari")
    st.write(f"Hadir bersamaan: {hadir_bersamaan} hari")
