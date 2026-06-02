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

def build_clean_db():
    return {
        "products": [
            {"id": "P001", "name_ar": "قاعدة كرسي RT50"},
            {"id": "P002", "name_ar": "ظهر كرسي RT50"}
        ],
        "parts": [
            # مكونات القاعدة الـ 8
            {"id": "B001", "name_ar": "مكون قاعدة 1", "product_id": "P001", "current_stock": 500, "danger_zone": 100},
            {"id": "B002", "name_ar": "مكون قاعدة 2", "product_id": "P001", "current_stock": 500, "danger_zone": 100},
            {"id": "B003", "name_ar": "مكون قاعدة 3", "product_id": "P001", "current_stock": 500, "danger_zone": 100},
            {"id": "B004", "name_ar": "مكون قاعدة 4", "product_id": "P001", "current_stock": 500, "danger_zone": 100},
            {"id": "B005", "name_ar": "مكون قاعدة 5", "product_id": "P001", "current_stock": 500, "danger_zone": 100},
            {"id": "B006", "name_ar": "مكون قاعدة 6", "product_id": "P001", "current_stock": 500, "danger_zone": 100},
            {"id": "B007", "name_ar": "مكون قاعدة 7", "product_id": "P001", "current_stock": 500, "danger_zone": 100},
            {"id": "B008", "name_ar": "مكون قاعدة 8", "product_id": "P001", "current_stock": 500, "danger_zone": 100},
            # مكونات الظهر الـ 5
            {"id": "S001", "name_ar": "جنب عدل", "product_id": "P002", "current_stock": 250, "danger_zone": 200},
            {"id": "S002", "name_ar": "جنب مايل", "product_id": "P002", "current_stock": 150, "danger_zone": 300},
            {"id": "S007", "name_ar": "رجل كبيرة", "product_id": "P002", "current_stock": 400, "danger_zone": 200},
            {"id": "S009", "name_ar": "دعامة", "product_id": "P002", "current_stock": 2000, "danger_zone": 500},
            {"id": "S010", "name_ar": "جنب يمين", "product_id": "P002", "current_stock": 350, "danger_zone": 400}
        ],
        "bom": [
            {"product_id": "P001", "part_id": "B001", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "B002", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "B003", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "B004", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "B005", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "B006", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "B007", "qty_per_unit": 1},
            {"product_id": "P001", "part_id": "B008", "qty_per_unit": 1},
            {"product_id": "P002", "part_id": "S001", "qty_per_unit": 1},
            {"product_id": "P002", "part_id": "S002", "qty_per_unit": 1},
            {"product_id": "P002", "part_id": "S007", "qty_per_unit": 2},
            {"product_id": "P002", "part_id": "S009", "qty_per_unit": 1},
            {"product_id": "P002", "part_id": "S010", "qty_per_unit": 1}
        ],
        "daily_logs": []
    }

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as db_f:
        json.dump(build_clean_db(), db_f, ensure_ascii=False, indent=2)

with open(DB_FILE, "r", encoding="utf-8") as db_f:
    try:
        db = json.load(db_f)
    except:
        db = build_clean_db()

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as db_f:
        json.dump(db, db_f, ensure_ascii=False, indent=2)

# القائمة الجانبية
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1e293b;'>⚙️ لوحة التحكم</h1>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("القائمة الرئيسية:", [
        "📊 لوحة المراقبة والرسوم البيانية", 
        "✏️ تسجيل حركة إنتاج وسحب", 
        "🛠️ خط إنتاج وتصنيع المكونات",
        "📋 سجل العمليات والتقارير",
        "🛠️ إعدادات المنتجات والـ BOM"
    ])

# ─── 1️⃣ لوحة المراقبة والرسوم البيانية ───
if page == "📊 لوحة المراقبة والرسوم البيانية":
    st.title("📊 نظام المراقبة الذكي ومؤشرات الأداء")
    
    product_dict = {p["name_ar"]: p["id"] for p in db.get("products", [])}
    filter_options = ["🔍 عرض كل المكونات"] + list(product_dict.keys())
    
    selected_filter = st.selectbox("🎯 تصفية عرض المخزون حسب المنتج المستهدف:", filter_options)
    st.markdown("---")
    
    all_parts = db.get("parts", [])
    if selected_filter == "🔍 عرض كل المكونات":
        filtered_parts = all_parts
        total_products_display = len(db.get("products", []))
    else:
        target_product_id = product_dict.get(selected_filter, "")
        filtered_parts = [p for p in all_parts if p.get("product_id") == target_product_id]
        total_products_display = 1

    total_parts_display = len(filtered_parts)
    danger_parts_display = sum(1 for p in filtered_parts if p.get("current_stock", 0) <= p.get("danger_zone", 0))
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">📦 المنتجات المشمولة بالعرض</div><div class="kpi-value">{total_products_display}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card success"><div class="kpi-label">🔧 أنواع المكونات المعروضة</div><div class="kpi-value">{total_parts_display}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card danger"><div class="kpi-label">🚨 قطع تحت حد الأمان (خطر)</div><div class="kpi-value" style="color:#ef4444">{danger_parts_display}</div></div>', unsafe_allow_html=True)

    st.markdown("<div class=\"section-title\">📈 تحليل حالة المخزون الحالي مقارنة بحد الخطر</div>", unsafe_allow_html=True)
    
    if total_parts_display > 0:
        df_parts = pd.DataFrame(filtered_parts)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="المخزون الحالي", x=df_parts["name_ar"], y=df_parts["current_stock"], marker_color="#3b82f6"))
        fig.add_trace(go.Scatter(name="حد الأمان (الخطر)", x=df_parts["name_ar"], y=df_parts["danger_zone"], mode="lines+markers", line=dict(color="#ef4444", width=3, dash="dash")))
        fig.update_layout(barmode="group", height=400, font=dict(family="Cairo"), margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 لا توجد قطع غيار مسجلة تحت هذا التصنيف حالياً.")

# ─── 2️⃣ تسجيل حركة إنتاج وسحب المنتجات النهائية ───
elif page == "✏️ تسجيل حركة إنتاج وسحب":
    st.title("✏️ قيد خطة الإنتاج اليومية والخصم التلقائي")
    
    if db.get("products"):
        prod_options = {p["name_ar"]: p["id"] for p in db["products"]}
        selected_prod = st.selectbox("اختر المنتج النهائي المستهدف للإنتاج اليوم:", list(prod_options.keys()))
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
        st.warning("⚠️ لا توجد منتجات مسجلة حتى الآن.")

# ─── 3️⃣ خط إنتاج وتصنيع المكونات ───
elif page == "🛠️ خط إنتاج وتصنيع المكونات":
    st.title("🛠️ خط تصنيع المكونات الداخلي ورفع التقارير")
    
    st.markdown("<div class=\"section-title\">📂 رفع تقرير الإنتاج اليومي للمكونات</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("اختر ملف التقرير اليومي (Excel أو CSV):", type=["xlsx", "csv", "xls"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_report = pd.read_csv(uploaded_file)
            else:
                df_report = pd.read_excel(uploaded_file)
                
            st.write("📊 معاينة البيانات المكتشفة داخل التقرير:")
            st.dataframe(df_report, use_container_width=True)
            
            date_col = st.selectbox("اختر العمود الممثل لـ (التاريخ):", df_report.columns, index=0 if "التاريخ" in df_report.columns else 0)
            part_col = st.selectbox("اختر العمود الممثل لـ (اسم المكون):", df_report.columns, index=0 if "المكون" in df_report.columns else 0)
            qty_col = st.selectbox("اختر العمود الممثل لـ (الكمية المصنعة):", df_report.columns, index=0 if "الكمية المصنعة" in df_report.columns else 0)
            
            if st.button("🚀 استيراد التقرير وتحديث أرصدة المخازن فوراً", type="primary"):
                success_count = 0
                for _, row in df_report.iterrows():
                    p_name = str(row[part_col]).strip()
                    p_qty = int(row[qty_col])
                    p_date = str(row[date_col])
                    
                    part = next((p for p in db["parts"] if p["name_ar"] == p_name), None)
                    if part:
                        part["current_stock"] += p_qty
                        db["daily_logs"].append({
                            "التاريخ": p_date,
                            "نوع الحركة": "إنتاج ورش داخلي (تقرير)",
                            "تفاصيل العملية": f"تصنيع وتوريد {p_qty} قطعة من ({p_name}) إلى المخزن"
                        })
                        success_count += 1
                
                save_db()
                st.success(f"✅ تم معالجة التقرير بنجاح! تم تحديث مخزون {success_count} حركة.")
                st.rerun()
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء قراءة الملف: {e}")
            
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.subheader("📝 إدخال إنتاج يدوي سريع")
    if db.get("parts"):
        part_options = {f"{p['name_ar']} (تابع لـ {next((pr['name_ar'] for pr in db['products'] if pr['id']==p.get('product_id')), 'غير محدد')})": p["id"] for p in db["parts"]}
        selected_part = st.selectbox("اختر المكون المحدد:", list(part_options.keys()))
        added_qty = st.number_input("الكمية المصنعة:", min_value=1, value=100, step=10)
        custom_date = st.date_input("التاريخ:", date.today())
        
        if st.button("➕ تسجيل الإنتاج اليدوي"):
            part_id = part_options[selected_part]
            part = next((p for p in db["parts"] if p["id"] == part_id), None)
            if part:
                part["current_stock"] += added_qty
                db["daily_logs"].append({
                    "التاريخ": str(custom_date),
                    "نوع الحركة": "إنتاج ورش داخلي (يدوي)",
                    "تفاصيل العملية": f"إدخال يدوي لإنتاج {added_qty} قطعة من: {selected_part.split(' (')[0]}"
                })
                save_db()
                st.success("✅ تم التحديث بنجاح!")
                st.rerun()

# ─── 4️⃣ سجل العمليات والتقارير ───
elif page == "📋 سجل العمليات والتقارير":
    st.title("📋 سجل الحركات والتقارير التاريخية")
    if db.get("daily_logs"):
        df_logs = pd.DataFrame(db["daily_logs"])
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد حركات مسجلة حتى الآن.")

# ─── 5️⃣ إعدادات المنتجات والـ BOM (محدثة بميزات الحذف والتطهير بالكامل) ───
elif page == "🛠️ إعدادات المنتجات والـ BOM":
    st.title("🛠️ إدارة وهيكلة النظام الفنية")
    
    sub_page = st.radio("اختر العملية المطلوبة:", [
        "➕ إضافة منتج جديد", 
        "🔧 إضافة مكون غيار للـ BOM",
        "❌ حذف منتج أو مكون من المنظومة",
        "🚨 خيار مطورين: إعادة ضبط وتطهير المخزن بالكامل"
    ])
    
    st.markdown("---")
    
    if sub_page == "➕ إضافة منتج جديد":
        new_prod_name = st.text_input("اسم المنتج النهائي الجديد:")
        if st.button("💾 حفظ المنتج"):
            if new_prod_name:
                new_id = f"P{len(db['products'])+1:03d}"
                db["products"].append({"id": new_id, "name_ar": new_prod_name})
                save_db()
                st.success("✅ تم حفظ المنتج!")
                st.rerun()
                
    elif sub_page == "🔧 إضافة مكون غيار للـ BOM":
        new_part_name = st.text_input("اسم قطعة الغيار الجديدة:")
        associated_prod = st.selectbox("تابع لأي منتج:", [p["name_ar"] for p in db["products"]])
        qty_needed = st.number_input("معدل الاستهلاك لكل وحدة من المنتج النهائي:", min_value=1, value=1)
        init_stock = st.number_input("الرصيد الافتتاحي في المخزن:", min_value=0, value=100)
        danger_limit = st.number_input("حد الأمان (الخطر):", min_value=10, value=50)
        
        if st.button("💾 ربط المكون بالـ BOM"):
            if new_part_name:
                p_id = next(p["id"] for p in db["products"] if p["name_ar"] == associated_prod)
                part_id = f"S{len(db['parts'])+1:03d}"
                db["parts"].append({"id": part_id, "name_ar": new_part_name, "product_id": p_id, "current_stock": init_stock, "danger_zone": danger_limit})
                db["bom"].append({"product_id": p_id, "part_id": part_id, "qty_per_unit": qty_needed})
                save_db()
                st.success("✅ تم إدراج وربط المكون!")
                st.rerun()

    elif sub_page == "❌ حذف منتج أو مكون من المنظومة":
        st.subheader("🗑️ قسم حذف البيانات الزائدة والمكررة")
        
        delete_target = st.selectbox("ماذا تريد أن تحذف؟", ["مسح منتج نهائي بالكامل", "مسح قطعة غيار / مكون محدد"])
        
        if delete_target == "مسح منتج نهائي بالكامل":
            prod_to_del = st.selectbox("اختر المنتج النهائي المراد حذفه نهائياً:", [p["name_ar"] for p in db.get("products", [])])
            st.warning(f"⚠️ انتبه: حذف منتج ({prod_to_del}) سيقوم بحذف المنتج فقط، وستظل المكونات فريدة لحين معالجتها أو مسحها.")
            
            if st.button("🗑️ تأكيد حذف المنتج نهائياً", type="primary"):
                p_id = next((p["id"] for p in db["products"] if p["name_ar"] == prod_to_del), None)
                if p_id:
                    db["products"] = [p for p in db["products"] if p["id"] != p_id]
                    # مسح الروابط من الـ BOM لهذا المنتج
                    db["bom"] = [b for b in db["bom"] if b["product_id"] != p_id]
                    save_db()
                    st.success("✅ تم حذف المنتج الفاينال وروابط الـ BOM الخاصة به بنجاح!")
                    st.rerun()
                    
        elif delete_target == "مسح قطعة غيار / مكون محدد":
            # عرض اسم المكون مع المنتج التابع له لسهولة التحديد الدقيق ومنع الخطأ
            part_map = {f"{p['name_ar']} (تابع لـ {next((pr['name_ar'] for pr in db['products'] if pr['id']==p.get('product_id')), 'غير محدد')})": p["id"] for p in db.get("parts", [])}
            
            if part_map:
                part_to_del = st.selectbox("اختر المكون التالف/المكرر المراد مسحه فوراً:", list(part_map.keys()))
                
                if st.button("🗑️ تأكيد حذف المكون من المخزن والـ BOM", type="primary"):
                    target_id = part_map[part_to_del]
                    db["parts"] = [p for p in db["parts"] if p["id"] != target_id]
                    db["bom"] = [b for b in db["bom"] if b["part_id"] != target_id]
                    save_db()
                    st.success("✅ تم بتر ومسح المكون تماماً من قواعد البيانات!")
                    st.rerun()
            else:
                st.info("لا توجد مكونات مسجلة حالياً لحذفها.")

    elif sub_page == "🚨 خيار مطورين: إعادة ضبط وتطهير المخزن بالكامل":
        st.subheader("🧼 عملية تطهير شاملة للملفات وتصحيح الأرقام")
        st.error("❗ تحذير: هذا الخيار سيمسح أي حركات أو تعديلات متداخلة بالخطأ في السيرفر ويعيد إجبار السيستم على الهيكل النظيف (5 للظهر و 8 للقاعدة) لتبدأ على نظافة وبدون أخطاء عدادات.")
        
        if st.button("🔥 اضغط هنا لتنفيذ إعادة ضبط المصنع الفوري"):
            db = build_clean_db()
            save_db()
            st.success("🧼 تم التطهير الشامل وإعادة السيستم للهيكل الأصلي الصحيح 100%! اذهب للوحة المراقبة لتشاهد دقة العدادات الآن.")
            st.rerun()
