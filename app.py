# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
from datetime import date
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="نظام المخزون الاحترافي",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم احترافي متقدم وعصري بالكامل
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght=400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background: #f8fafc; }
    .kpi-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); text-align: center; border-bottom: 5px solid #3b82f6; }
    .kpi-card.danger { border-bottom-color: #ef4444; }
    .kpi-card.success { border-bottom-color: #10b981; }
    .kpi-value { font-size: 2.6rem; font-weight: 700; color: #1e293b; margin: 5px 0; }
    .kpi-label { font-size: 1rem; color: #64748b; font-weight: 600; }
    .section-title { background: #1e293b; color: white; padding: 10px 20px; border-radius: 8px; font-size: 1.2rem; margin: 20px 0; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

DB_FILE = "inventory_db.json"

# إرجاع البيانات الافتراضية مع الحفاظ على مرونة النظام لإضافة منتجات جديدة
def build_default_db():
    return {
        "products": [
            {"id": "P001", "name_ar": "قاعدة كرسي RT50"},
            {"id": "P002", "name_ar": "ظهر كرسي RT50"}
        ],
        "parts": [
            {"id": "S001", "name_ar": "جنب عدل", "product_id": "P001", "current_stock": 250, "danger_zone": 200},
            {"id": "S002", "name_ar": "جنب مايل", "product_id": "P001", "current_stock": 150, "danger_zone": 300},
            {"id": "S007", "name_ar": "رجل كبيرة", "product_id": "P001", "current_stock": 400, "danger_zone": 200},
            {"id": "S009", "name_ar": "دعامة", "product_id": "P002", "current_stock": 2000, "danger_zone": 500},
            {"id": "S010", "name_ar": "جنب يمين", "product_id": "P002", "current_stock": 350, "danger_zone": 400}
        ],
        "bom": [
            {"product_id": "P001", "part_id": "S001", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "S002", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "S007", "qty_per_unit": 2},
            {"product_id": "P002", "part_id": "S009", "qty_per_unit": 1},
            {"product_id": "P002", "part_id": "S010", "qty_per_unit": 1}
        ],
        "daily_logs": []
    }

# التحقق من الملف أو إنشائه بالبيانات القديمة المفصلة
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as db_f:
        json.dump(build_default_db(), db_f, ensure_ascii=False, indent=2)

with open(DB_FILE, "r", encoding="utf-8") as db_f:
    try:
        db = json.load(db_f)
        # إذا تسبب التحديث السابق في جعل القوائم فارغة تماماً، نعيد شحنها بالبيانات الأساس
