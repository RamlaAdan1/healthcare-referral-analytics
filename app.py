import streamlit as st

st.set_page_config(
    page_title="Healthcare Referral Intelligence Platform",
    layout="wide"
)

st.title("Healthcare Referral Intelligence Platform")
st.caption("End-to-end analytics for referral efficiency, delays and performance")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Referrals", "12,458", "+12.6%")
col2.metric("Average Waiting Time", "6.2 hrs", "-0.8 hrs")
col3.metric("Completion Rate", "86.7%", "+4.3%")
col4.metric("Rejected Referrals", "612", "-8.1%")
