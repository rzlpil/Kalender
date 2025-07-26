import streamlit as st
import calendar
from datetime import datetime

st.title('Kalender')

st.sidebar.header("Select Date")

year = st.sidebar.number_input("Enter Year", min_value=1900, max_value = 3000, value=datetime.now().year)
month = st.sidebar.selectbox('Select Month', list(calendar.month_name)[1:],index=datetime.now().month-1)
if year and month:
  st.subheader(f"Calendar {month}/{year}")
  month_number = list(calendar.month_name).index(month)
  cal_text = calendar.month(year, month_number)
  st.code(cal_text, language='text')
  
