import streamlit as st

st.set_page_config(page_title="Trust Calibration", layout="wide")

from awareml.ui_v2.phase16_morten_v2 import phase16_trust_calibration_page_v2

phase16_trust_calibration_page_v2()
