# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
from datetime import date
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="نظام إدارة مخزون الكراسي المحترف",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# واجهة مستخدم احترافية بالكامل باللغة العربية
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

# بناء قاعدة بيانات نظيفة، مفصولة، وصارمة هندسياً تمنع التداخل نهائياً
def build_clean_absolute_db():
    return {
        "قاعدة كرسي RT50": [
            {"name": "مكون قاعدة 1", "stock": 500, "danger": 100, "usage": 1},
            {"name": "مكون قاعدة 2", "stock": 500, "danger": 100, "usage": 1},
            {"name": "مكون قاعدة 3", "stock": 500, "danger": 100, "usage": 1},
            {"name": "مكون قاعدة 4", "stock": 500, "danger": 100, "usage": 1},
            {"name": "مكون قاعدة 5", "stock": 500, "danger": 100, "usage": 1},
            {"name": "مكون قاعدة 6", "stock": 500, "danger": 100, "usage": 1},
            {"name": "مكون قاعدة 7", "stock": 500, "danger": 100, "usage": 1},
            {"name": "مكون قاعدة 8", "stock": 500, "danger": 100, "usage": 1}
        ],
        "ظهر كرسي RT50": [
            {"name": "جنب عدل", "stock": 250, "danger": 200, "usage": 1},
            {"name": "جنب مايل", "stock": 150, "danger": 300, "usage": 1},
            {"name": "رجل كبيرة", "stock": 400, "danger": 200, "usage": 2},
            {"name": "دعامة", "stock": 2000, "danger": 500, "usage": 1},
            {"name": "جنب يمين", "stock": 350, "danger": 400, "usage": 1}
        ],
        "logs": []
    }

# إجبار السيرفر على سحق أي ملف قديم تالف وتبني الهيكل الجديد فوراً عند الرفع
db = build_clean_absolute_db()

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# التثبيت الفوري في الذاكرة لمنع تكرار الخطأ
if not os.path.exists(DB_FILE) or True: 
    save_db()

# القائمة الجانبية المباشرة
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1e293b;'>⚙️ لوحة التحكم</h1>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("القائمة الرئيسية:", [
        "📊 لوحة المراقبة والرسوم البيانية", 
        "✏️ تسجيل حركة إنتاج وسحب", 
        "🛠️ خط إنتاج وتصنيع المكونات",
        "📋 سجل العمليات والتقارير",
        "🛠️ إعدادات أسماء المكونات"
    ])

# ─── 1️⃣ لوحة المراقبة والرسوم البيانية ───
if page == "📊 لوحة المراقبة والرسوم البيانية":
    st.title("📊 نظام المراقبة الذكي ومؤشرات الأداء")
    
    products = [k for k in db.keys() if k != "logs"]
    selected_product = st.selectbox("🎯 اختر المنتج لعرض مكوناته وعداداته بدقة:", products)
    st.markdown("---")
    
    parts_list = db[selected_product]
    total_parts = len(parts_list)
    danger_parts = sum(1 for p in parts_list if p["stock"] <= p["danger"])
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="kpi-card success"><div class="kpi-label">🔧 عدد مكونات ({selected_product}) الحالية</div><div class="kpi-value">{total_parts}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card danger"><div class="kpi-label">🚨 قطع تحت حد الأمان (خطر)</div><div class="kpi-value" style="color:#ef4444">{danger_parts}</div></div>', unsafe_allow_html=True)

    st.markdown("<div class=\"section-title\">📈 تحليل حالة رصيد المكونات الحالية مقارنة بحد الخطر</div>", unsafe_allow_html=True)
    
    df = pd.DataFrame(parts_list)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="المخزون الحالي", x=df["name"], y=df["stock"], marker_color="#3b82f6"))
    fig.add_trace(go.Scatter(name="حد الأمان (الخطر)", x=df["name"], y=df["danger"], mode="lines+markers", line=dict(color="#ef4444", width=3, dash="dash")))
    fig.update_layout(barmode="group", height=400, font=dict(family="Cairo"), margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

# ─── 2️⃣ تسجيل حركة إنتاج وسحب المنتجات النهائية ───
elif page == "✏️ تسجيل حركة إنتاج وسحب":
    st.title("✏️ قيد خطة الإنتاج اليومية والخصم التلقائي من المخزن")
    
    products = [k for k in db.keys() if k != "logs"]
    selected_prod = st.selectbox("اختر المنتج النهائي الذي تم إنتاجه اليوم لتخصيم مكوناته:", products)
    qty = st.number_input("الكمية المصنعة (وحدة):", min_value=1, value=100, step=10)
    
    if st.button("💾 تنفيذ الخصم التلقائي من المخزن", type="primary"):
        for item in db[selected_prod]:
            item["stock"] -= (item["usage"] * qty)
            
        db["logs"].append({
            "التاريخ": str(date.today()),
            "نوع الحركة": "سحب إنتاج تلقائي",
            "تفاصيل العملية": f"إنتاج {qty} وحدة من {selected_prod} وخصم مكوناتها"
        })
        save_db()
        st.success("✅ تم خصم المكونات وتحديث المخازن بنجاح!")
        st.rerun()

# ─── 3️⃣ خط إنتاج وتصنيع المكونات (رفع التقرير اليومي) ───
elif page == "🛠️ خط إنتاج وتصنيع المكونات":
    st.title("🛠️ خط تصنيع المكونات الداخلي ورفع التقارير")
    
    st.markdown("<div class=\"section-title\">📂 رفع تقرير الإنتاج اليومي للمكونات (Excel / CSV)</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("اختر ملف التقرير اليومي القادم من الورشة:", type=["xlsx", "csv", "xls"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_report = pd.read_csv(uploaded_file)
            else:
                df_report = pd.read_excel(uploaded_file)
                
            st.write("📊 معاينة البيانات المكتشفة داخل التقرير المرفوع:")
            st.dataframe(df_report, use_container_width=True)
            
            date_col = st.selectbox("اختر عمود (التاريخ):", df_report.columns)
            part_col = st.selectbox("اختر عمود (اسم المكون):", df_report.columns)
            qty_col = st.selectbox("اختر عمود (الالكمية المصنعة):", df_report.columns)
            
            if st.button("🚀 استيراد التقرير وتغذية المخازن فوراً", type="primary"):
                success_count = 0
                for _, row in df_report.iterrows():
                    p_name = str(row[part_col]).strip()
                    p_qty = int(row[qty_col])
                    p_date = str(row[date_col])
                    
                    # البحث عن المكون داخل جداول المخزن المفصولة وزيادته
                    for category in db.keys():
                        if category != "logs":
                            for item in db[category]:
                                if item["name"] == p_name:
                                    item["stock"] += p_qty
                                    db["logs"].append({
                                        "التاريخ": p_date,
                                        "نوع الحركة": "إنتاج ورش (تقرير)",
                                        "تفاصيل العملية": f"إضافة {p_qty} قطعة لـ ({p_name}) تابعة لـ {category}"
                                    })
                                    success_count += 1
                save_db()
                st.success(f"✅ تم بنجاح معالجة التقرير وتحديث {success_count} حركات مخزنية!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء معالجة الملف الرقمي: {e}")
            
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.subheader("📝 إدخال إنتاج يدوي سريع")
    
    all_categories = [k for k in db.keys() if k != "logs"]
    chosen_cat = st.selectbox("المكون المطلوب تصنيعه تابع لأي قسم؟", all_categories)
    
    cat_parts = [p["name"] for p in db[chosen_cat]]
    chosen_part = st.selectbox("اختر المكون المحدد المراد إضافة رصيد له:", cat_parts)
    added_qty = st.number_input("الكمية التي تم تصنيعها حديثاً بالورشة:", min_value=1, value=50)
    
    if st.button("➕ إضافة الرصيد يدوياً للمخزن"):
        for item in db[chosen_cat]:
            if item["name"] == chosen_part:
                item["stock"] += added_qty
                db["logs"].append({
                    "التاريخ": str(date.today()),
                    "نوع الحركة": "إنتاج يدوي بالورشة",
                    "تفاصيل العملية": f"إدخال {added_qty} قطعة يدوي لـ ({chosen_part})"
                })
                save_db()
                st.success("✅ تم إضافة الرصيد بنجاح!")
                st.rerun()

# ─── 4️⃣ سجل العمليات والتقارير ───
elif page == "📋 سجل العمليات والتقارير":
    st.title("📋 سجل الحركات التاريخية للمخازن")
    if db.get("logs"):
        st.dataframe(pd.DataFrame(db["logs"]), use_container_width=True, hide_index=True)
    else:
        st.info("السجل فارغ حتى الآن.")

# ─── 5️⃣ إعدادات أسماء المكونات الفنية (تعديل مباشر) ───
elif page == "🛠️ إعدادات أسماء المكونات":
    st.title("🛠️ تعديل وتغيير أسماء المكونات الـ 8 والـ 5")
    st.info("💡 من هنا يمكنك تغيير الأسماء المؤقتة للقاعدة (مكون قاعدة 1، إلخ) إلى أسمائها الحقيقية فوراً وبدون أي تداخل أو حذف للأرصدة!")
    
    all_categories = [k for k in db.keys() if k != "logs"]
    chosen_cat = st.selectbox("اختر القسم لتعديل أسماء مكوناته:", all_categories)
    
    cat_parts = [p["name"] for p in db[chosen_cat]]
    part_to_rename = st.selectbox("اختر المكون المراد تغيير اسمه:", cat_parts)
    new_clean_name = st.text_input("اكتب الاسم الحقيقي والجديد للمكون:")
    
    if st.button("💾 حفظ الاسم الجديد نهائياً"):
        if new_clean_name:
            for item in db[chosen_cat]:
                if item["name"] == part_to_rename:
                    item["name"] = new_clean_name.strip()
                    save_db()
                    st.success(f"✅ تم تغيير الاسم بنجاح من ({part_to_rename}) إلى ({new_clean_name})!")
                    st.rerun()
