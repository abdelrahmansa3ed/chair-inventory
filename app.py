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

# قاعدة بيانات مرنة تبدأ فارغة لتستوعب أي موديل (RT50، RT60، إلخ)
def build_default_db():
    return {
        "products": [],
        "parts": [],
        "bom": [],
        "daily_logs": []
    }

# إذا لم تكن قاعدة البيانات موجودة، نصنع واحدة مرنة ونظيفة
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as db_f:
        json.dump(build_default_db(), db_f, ensure_ascii=False, indent=2)

with open(DB_FILE, "r", encoding="utf-8") as db_f:
    try:
        db = json.load(db_f)
    except:
        db = build_default_db()

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as db_f:
        json.dump(db, db_f, ensure_ascii=False, indent=2)

# القائمة الجانبية المطورة
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1e293b;'>⚙️ لوحة التحكم</h1>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("القائمة الرئيسية:", [
        "📊 لوحة المراقبة والرسوم البيانية", 
        "✏️ تسجيل حركة إنتاج وسحب", 
        "📦 إدارة التوريدات والشحنات",
        "📋 سجل العمليات والتقارير",
        "🛠️ إعدادات المنتجات والـ BOM"
    ])

# ─── 1️⃣ لوحة المراقبة والرسوم البيانية ───
if page == "📊 لوحة المراقبة والرسوم البيانية":
    st.title("📊 نظام المراقبة الذكي ومؤشرات الأداء")
    
    total_products = len(db.get("products", []))
    total_parts = len(db.get("parts", []))
    danger_parts = sum(1 for p in db.get("parts", []) if p["current_stock"] <= p["danger_zone"])
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">📦 إجمالي المنتجات النهائية</div><div class="kpi-value">{total_products}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card success"><div class="kpi-label">🔧 إجمالي أنواع المكونات</div><div class="kpi-value">{total_parts}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card danger"><div class="kpi-label">🚨 قطع في منطقة الخطر</div><div class="kpi-value" style="color:#ef4444">{danger_parts}</div></div>', unsafe_allow_html=True)

    st.markdown("<div class=\"section-title\">📈 تحليل حالة المخزون الحالي مقارنة بحد الخطر</div>", unsafe_allow_html=True)
    
    if total_parts > 0:
        df_parts = pd.DataFrame(db["parts"])
        fig = go.Figure()
        fig.add_trace(go.Bar(name="المخزون الحالي", x=df_parts["name_ar"], y=df_parts["current_stock"], marker_color="#3b82f6"))
        fig.add_trace(go.Scatter(name="حد الأمان (الخطر)", x=df_parts["name_ar"], y=df_parts["danger_zone"], mode="lines+markers", line=dict(color="#ef4444", width=3, dash="dash")))
        fig.update_layout(barmode="group", height=400, font=dict(family="Cairo"), margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 المخزن فارغ حالياً. اذهب إلى صفحة الإعدادات لإضافة منتجاتك ومكوناتها أولاً ليظهر الرسم البياني هنا!")

# ─── 2️⃣ تسجيل حركة إنتاج وسحب ───
elif page == "✏️ تسجيل حركة إنتاج وسحب":
    st.title("✏️ قيد خطة الإنتاج اليومية والخصم التلقائي")
    
    if db.get("products"):
        prod_options = {p["name_ar"]: p["id"] for p in db["products"]}
        selected_prod = st.selectbox("اختر المنتج النهائي المستهدف:", list(prod_options.keys()))
        qty = st.number_input("الكمية التي تم تصنيعها (وحدة):", min_value=1, value=100, step=10)
        
        if st.button("💾 تنفيذ سحب المكونات وحفظ الحركة", type="primary"):
            prod_id = prod_options[selected_prod]
            bom_items = [b for b in db.get("bom", []) if b["product_id"] == prod_id]
            
            if bom_items:
                for item in bom_items:
                    part = next((p for p in db["parts"] if p["id"] == item["part_id"]), None)
                    if part:
                        part["current_stock"] -= (item["qty_per_unit"] * qty)
                        
                db["daily_logs"].append({
                    "التاريخ": str(date.today()),
                    "نوع الحركة": "سحب إنتاج اليوم",
                    "تفاصيل العملية": f"إنتاج {qty} وحدة من {selected_prod}"
                })
                save_db()
                st.success("✅ تم تحديث المخزن وتسجيل الحركة بنجاح!")
                st.rerun()
            else:
                st.error("❌ هذا المنتج ليس له مكونات مسجلة في الـ BOM حتى الآن!")
    else:
        st.warning("⚠️ لا توجد منتجات مسجلة حتى الآن. أضف منتجاً أولاً من صفحة الإعدادات.")

# ─── 3️⃣ إدارة التوريدات والشحنات ───
elif page == "📦 إدارة التوريدات والشحنات":
    st.title("📦 تسجيل شحنات التوريد الجديدة للمخزن")
    
    if db.get("parts"):
        part_options = {p["name_ar"]: p["id"] for p in db["parts"]}
        selected_part = st.selectbox("اختر المكون المستلم:", list(part_options.keys()))
        added_qty = st.number_input("الكمية الموردة الجديدة:", min_value=1, value=500, step=50)
        
        if st.button("➕ إضافة الوارد للمخازن", type="primary"):
            part_id = part_options[selected_part]
            part = next((p for p in db["parts"] if p["id"] == part_id), None)
            if part:
                part["current_stock"] += added_qty
                db["daily_logs"].append({
                    "التاريخ": str(date.today()),
                    "نوع الحركة": "توريد خارجي للمخزن",
                    "تفاصيل العملية": f"إضافة {added_qty} وحدة للمكون: {selected_part}"
                })
                save_db()
                st.success(f"✅ تم توريد {added_qty} شحنة جديدة لـ {selected_part}!")
                st.rerun()
    else:
        st.warning("⚠️ لا توجد قطع أو مكونات غيار مسجلة بعد. يرجى إضافتها وربطها بالمنتجات أولاً.")

# ─── 4️⃣ سجل العمليات والتقارير ───
elif page == "📋 سجل العمليات والتقارير":
    st.title("📋 سجل الحركات والتقارير التاريخية للمخازن")
    
    if db.get("daily_logs"):
        df_logs = pd.DataFrame(db["daily_logs"])
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
        
        csv = df_logs.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تحميل سجل الحركات كملف Excel (CSV)", data=csv, file_name="inventory_report.csv", mime="text/csv")
    else:
        st.info("لا توجد حركات مسجلة حتى الآن.")

# ─── 5️⃣ إعدادات المنتجات والـ BOM ───
elif page == "🛠️ إعدادات المنتجات والـ BOM":
    st.title("🛠️ إدارة هيكلة المنتجات والمكونات الفنية")
    
    sub_page = st.radio(
        "اختر العملية التي تريد القيام بها الآن:",
        ["➕ إضافة منتج نهائي جديد (مثال: كرسي RT50، كرسي RT60، كرسي طبي...)", 
         "🔧 إضافة مكون غيار جديد وتحديد معدل استهلاكه بالـ BOM"]
    )
    
    st.markdown("---")
    
    if sub_page == "➕ إضافة منتج نهائي جديد (مثال: كرسي RT50، كرسي RT60، كرسي طبي...)":
        st.subheader("📦 إضافة منتج نهائي جديد لشجرة العائلة")
        new_prod_name = st.text_input("اكتب اسم المنتج النهائي الجديد هنا (مثل: كرسي RT60):")
        if st.button("💾 حفظ المنتج الجديد في النظام", type="primary"):
            if new_prod_name:
                new_id = f"P{len(db['products'])+1:03d}"
                db["products"].append({"id": new_id, "name_ar": new_prod_name})
                save_db()
                st.success(f"✅ تمت إضافة المنتج الجديد ({new_prod_name}) بنجاح للمنظومة!")
                st.rerun()
            else:
                st.error("❌ فضلاً اكتب اسم المنتج أولاً قبل الحفظ.")
                
    elif sub_page == "🔧 إضافة مكون غيار جديد وتحديد معدل استهلاكه بالـ BOM":
        st.subheader("🔧 ربط قطع الغيار والمكونات بالمنتجات")
        if db.get("products"):
            new_part_name = st.text_input("اسم قطعة الغيار / المكون الفني الجديد (مثل: نجمة كرسي):")
            associated_prod = st.selectbox("تابع لأي منتج نهائي وموديل:", [p["name_ar"] for p in db["products"]])
            qty_needed = st.number_input("معدل استهلاك هذه القطعة (لكل وحدة واحدة من المنتج):", min_value=1, value=1)
            init_stock = st.number_input("الرصيد الافتتاحي المتوفر حالياً بالمخزن:", min_value=0, value=100)
            danger_limit = st.number_input("نقطة إعادة الطلب والحد الخطر (حد الأمان):", min_value=10, value=50)
            
            if st.button("💾 إدراج القطعة وتحديث شجرة المنتج (BOM)", type="primary"):
                if new_part_name:
                    p_id = next(p["id"] for p in db["products"] if p["name_ar"] == associated_prod)
                    part_id = f"S{len(db['parts'])+1:03d}"
                    db["parts"].append({"id": part_id, "name_ar": new_part_name, "product_id": p_id, "current_stock": init_stock, "danger_zone": danger_limit})
                    db["bom"].append({"product_id": p_id, "part_id": part_id, "qty_per_unit": qty_needed})
                    save_db()
                    st.success(f"✅ تم تسجيل المكون ({new_part_name}) وربطه بـ ({associated_prod}) بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ فضلاً اكتب اسم قطعة الغيار أولاً.")
        else:
            st.info("💡 يجب عليك أولاً اختيار 'إضافة منتج نهائي جديد' من الأعلى قبل أن تتمكن من إضافة أجزاء تابعة له.")
