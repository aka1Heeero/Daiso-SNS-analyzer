import streamlit as st
import requests
import openpyxl
import re
import io
import gspread
import pandas as pd
import altair as alt
import concurrent.futures
from datetime import datetime, date, timedelta
from google.oauth2.service_account import Credentials
from transformers import pipeline
from collections import Counter

# ============================
# 페이지 설정
# ============================
st.set_page_config(
    page_title="DAISO-SNS Issue Finder",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# CSS
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --primary:    #0066CC;
    --primary-lt: #E8F1FB;
    --primary-md: #CCE0F5;
    --bg:         #F8F9FB;
    --bg-white:   #FFFFFF;
    --border:     #E2E8F0;
    --border2
