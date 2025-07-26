from pymongo import MongoClient
import streamlit as st

# Ambil dari secrets
client = MongoClient(st.secrets["MONGO_URI"])

# Tentukan database dan collection (otomatis dibuat saat insert)
db = client["jadwal_kantor"]
collection = db["kehadiran_rizal"]

# Menyimpan data ke collection
collection.insert_one({
    "tanggal": "2025-07-26",
    "hadir": True,
})
