"""
Chair Manufacturing Inventory Management System
نظام إدارة مخزون تصنيع الكراسي
"""

import streamlit as st
import pandas as pd
import json
import base64
import anthropic
from datetime import date, datetime
import plotly.graph_objects as go
import plotly.express as px
import os
import io

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="نظام مخزون تصنيع الكراسي | Chair Inventory",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS  (RTL-aware, professional dark-accented theme)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }

    .stApp { background: #f4f6f9; }

    /* ── KPI Cards ── */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,.08);
        text-align: center;
        border-top: 4px solid #2563eb;
    }
    .kpi-card.danger  { border-top-color: #dc2626; }
    .kpi-card.warning { border-top-color: #f59e0b; }
    .kpi-card.success { border-top-color: #16a34a; }
    .kpi-value { font-size: 2.4rem; font-weight: 700; margin: 6px 0; }
    .kpi-label { font-size: .9rem; color: #6b7280; }

    /* ── Alert Banners ── */
    .alert-danger  { background:#fee2e2; border-left:5px solid #dc2626;
                     color:#991b1b; padding:12px 16px; border-radius:8px; margin:6px 0; }
    .alert-warning { background:#fef3c7; border-left:5px solid #f59e0b;
                     color:#92400e; padding:12px 16px; border-radius:8px; margin:6px 0; }
    .alert-ok      { background:#dcfce7; border-left:5px solid #16a34a;
                     color:#166534; padding:12px 16px; border-radius:8px; margin:6px 0; }

    /* ── Section Headers ── */
    .section-header {
        font-size:1.3rem; font-weight:700; color:#1e3a5f;
        border-bottom:2px solid #2563eb; padding-bottom:6px; margin:18px 0 12px;
    }

    /* ── Inventory Table rows ── */
    .tbl-danger  { background:#fee2e2 !important; }
    .tbl-warning { background:#fef3c7 !important; }

    div[data-testid="stSidebar"] { background: #1e3a5f; }
    div[data-testid="stSidebar"] * { color: white !important; }
    div[data-testid="stSidebar"] .stSelectbox label,
    div[data-testid="stSidebar"] .stTextInput label { color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# DATABASE  (SQLite via pandas + JSON state stored in session)
# ─────────────────────────────────────────────────────────────
DB_FILE = "inventory_db.json"


def load_db() -> dict:
    """Load database from JSON file, or create default schema."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return build_default_db()


def save_db(db: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2, default=str)


def build_default_db() -> dict:
    """
    Build the initial database from the real Excel data provided:
      - Products: قاعدة RT50 و ظهر RT50
      - BOM per product with معدل السحب (consumption rate)
      - Opening stock from الرصيد قبل السحب والانتاج (December sheet)
      - Safety stock (danger_zone) = ~30% of opening stock
    """
    products = [
        {"id": "P001", "name_ar": "قاعدة كرسي RT50",  "name_en": "Chair Base RT50"},
        {"id": "P002", "name_ar": "ظهر كرسي RT50",    "name_en": "Chair Back RT50"},
    ]

    # Sub-parts with opening stock & safety-stock thresholds
    # Extracted directly from your Excel sheet (December opening balances)
    parts = [
        # قاعدة RT50 parts
        {"id": "S001", "name_ar": "جنب عدل",   "name_en": "Side Straight", "product_id": "P001",
         "current_stock": 100,  "danger_zone": 200,  "unit": "pcs"},
        {"id": "S002", "name_ar": "جنب مايل",  "name_en": "Side Angled",   "product_id": "P001",
         "current_stock": 500,  "danger_zone": 300,  "unit": "pcs"},
        {"id": "S003", "name_ar": "حرف Z كبير","name_en": "Z-Bar Large",   "product_id": "P001",
         "current_stock": 1000, "danger_zone": 400,  "unit": "pcs"},
        {"id": "S004", "name_ar": "حرف Z صغير","name_en": "Z-Bar Small",   "product_id": "P001",
         "current_stock": 2000, "danger_zone": 500,  "unit": "pcs"},
        {"id": "S005", "name_ar": "زاوية",     "name_en": "Corner Bracket","product_id": "P001",
         "current_stock": 2500, "danger_zone": 600,  "unit": "pcs"},
        {"id": "S006", "name_ar": "حرف U",     "name_en": "U-Bar",         "product_id": "P001",
         "current_stock": 4000, "danger_zone": 800,  "unit": "pcs"},
        {"id": "S007", "name_ar": "رجل كبيرة", "name_en": "Leg Large",     "product_id": "P001",
         "current_stock": 150,  "danger_zone": 200,  "unit": "pcs"},
        {"id": "S008", "name_ar": "رجل مايلة", "name_en": "Leg Angled",    "product_id": "P001",
         "current_stock": 100,  "danger_zone": 200,  "unit": "pcs"},
        # ظهر RT50 parts
        {"id": "S009", "name_ar": "دعامة",      "name_en": "Support Bar",   "product_id": "P002",
         "current_stock": 2000, "danger_zone": 500,  "unit": "pcs"},
        {"id": "S010", "name_ar": "جنب يمين",  "name_en": "Right Side",    "product_id": "P002",
         "current_stock": 1500, "danger_zone": 400,  "unit": "pcs"},
        {"id": "S011", "name_ar": "جنب شمال",  "name_en": "Left Side",     "product_id": "P002",
         "current_stock": 1500, "danger_zone": 400,  "unit": "pcs"},
        {"id": "S012", "name_ar": "مسطرة",     "name_en": "Ruler Bar",     "product_id": "P002",
         "current_stock": 1500, "danger_zone": 400,  "unit": "pcs"},
        {"id": "S013", "name_ar": "دليل الهيد","name_en": "Head Guide",    "product_id": "P002",
         "current_stock": 2000, "danger_zone": 500,  "unit": "pcs"},
    ]

    # Bill Of Materials  (part_id → qty_per_finished_product)
    # معدل السحب = consumption rate per chair produced
    bom = [
        # قاعدة RT50
        {"product_id": "P001", "part_id": "S001", "qty_per_unit": 1},
        {"product_id": "P001", "part_id": "S002", "qty_per_unit": 1},
        {"product_id": "P001", "part_id": "S003", "qty_per_unit": 1},
        {"product_id": "P001", "part_id": "S004", "qty_per_unit": 1},
        {"product_id": "P001", "part_id": "S005", "qty_per_unit": 1},
        {"product_id": "P001", "part_id": "S006", "qty_per_unit": 2},  # حرف U × 2
        {"product_id": "P001", "part_id": "S007", "qty_per_unit": 1},
        {"product_id": "P001", "part_id": "S008", "qty_per_unit": 1},
        # ظهر RT50
        {"product_id": "P002", "part_id": "S009", "qty_per_unit": 1},
        {"product_id": "P002", "part_id": "S010", "qty_per_unit": 1},
        {"product_id": "P002", "part_id": "S011", "qty_per_unit": 1},
        {"product_id": "P002", "part_id": "S012", "qty_per_unit": 1},
        {"product_id": "P002", "part_id": "S013", "qty_per_unit": 2},  # دليل الهيد × 2
    ]

    daily_logs = []   # [{date, product_id, qty_produced, deductions:[{part_id,qty}]}]

    return {"products": products, "parts": parts, "bom": bom, "daily_logs": daily_logs}


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def get_part(db, part_id):
    return next((p for p in db["parts"] if p["id"] == part_id), None)


def get_product(db, product_id):
    return next((p for p in db["products"] if p["id"] == product_id), None)


def get_bom(db, product_id):
    return [b for b in db["bom"] if b["product_id"] == product_id]


def stock_status(current, danger):
    """Returns 'danger', 'warning', or 'ok'."""
    if current <= 0:
        return "danger"
    if current <= danger:
        return "danger"
    if current <= danger * 1.5:
        return "warning"
    return "ok"


# ─────────────────────────────────────────────────────────────
# INVENTORY DEDUCTION ENGINE
# ─────────────────────────────────────────────────────────────
def apply_production(db: dict, product_id: str, qty_produced: int,
                     log_date: str = None) -> dict:
    """
    Deduct sub-parts from stock based on BOM and production quantity.
    Returns a summary dict.
    """
    bom_rows = get_bom(db, product_id)
    if not bom_rows:
        return {"success": False, "error": f"No BOM found for {product_id}"}

    deductions = []
    alerts = []

    for row in bom_rows:
        part = get_part(db, row["part_id"])
        if not part:
            continue
        deduct_qty = row["qty_per_unit"] * qty_produced
        part["current_stock"] -= deduct_qty
        status = stock_status(part["current_stock"], part["danger_zone"])
        deductions.append({
            "part_id": part["id"],
            "part_name": part["name_ar"],
            "deducted": deduct_qty,
            "remaining": part["current_stock"],
            "danger_zone": part["danger_zone"],
            "status": status,
        })
        if status in ("danger", "warning"):
            alerts.append(part["name_ar"])

    log_entry = {
        "date": log_date or str(date.today()),
        "product_id": product_id,
        "product_name": get_product(db, product_id)["name_ar"],
        "qty_produced": qty_produced,
        "deductions": deductions,
        "timestamp": str(datetime.now()),
    }
    db["daily_logs"].append(log_entry)
    save_db(db)

    return {"success": True, "log": log_entry, "alerts": alerts}


# ─────────────────────────────────────────────────────────────
# OCR  — Claude Vision (claude-sonnet-4-20250514)
# ─────────────────────────────────────────────────────────────
def ocr_production_report(image_bytes: bytes, mime_type: str, db: dict) -> list[dict]:
    """
    Send the production report image to Claude Vision and extract
    product quantities using the actual Arabic product names from the DB.
    Returns list of {product_id, product_name, qty_produced}.
    """
    product_list = "\n".join(
        f"- ID={p['id']}: {p['name_ar']} ({p['name_en']})"
        for p in db["products"]
    )

    prompt = f"""You are an OCR assistant for a chair manufacturing factory in Egypt.
Analyze this daily production report image and extract the quantities produced for each product.

Known products in our system:
{product_list}

Instructions:
1. Look for Arabic product names or any quantities listed in the report.
2. Match them to the product IDs above.
3. Return ONLY valid JSON (no markdown, no explanation), as an array of objects like:
[
  {{"product_id": "P001", "product_name": "قاعدة كرسي RT50", "qty_produced": 50}},
  {{"product_id": "P002", "product_name": "ظهر كرسي RT50",   "qty_produced": 30}}
]
4. If you cannot read a product clearly, skip it.
5. If the image contains a table with daily numbers, sum the values for all days visible.
6. Return an empty array [] if nothing is readable.
"""

    client = anthropic.Anthropic()
    img_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                                              "media_type": mime_type,
                                              "data": img_b64}},
                {"type": "text", "text": prompt},
            ]
        }]
    )

    raw = response.content[0].text.strip()
    # Strip possible markdown fences
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────────────────────────
if "db" not in st.session_state:
    st.session_state.db = load_db()

db = st.session_state.db

# ── Sidebar Navigation ──────────────────────────────────────
with st.sidebar:
    st.markdown("## 🪑 نظام مخزون الكراسي")
    st.markdown("---")
    page = st.radio("القائمة الرئيسية", [
        "📊 لوحة التحكم",
        "📷 رفع تقرير الإنتاج",
        "✏️ إدخال يدوي",
        "📦 إدارة المخزون",
        "📋 سجل العمليات",
        "⚙️ إعدادات المنتجات",
    ])
    st.markdown("---")

    # Quick danger count in sidebar
    danger_count = sum(
        1 for p in db["parts"]
        if stock_status(p["current_stock"], p["danger_zone"]) == "danger"
    )
    warning_count = sum(
        1 for p in db["parts"]
        if stock_status(p["current_stock"], p["danger_zone"]) == "warning"
    )
    if danger_count:
        st.markdown(f'<div class="alert-danger">🚨 {danger_count} قطعة في المنطقة الحمراء</div>',
                    unsafe_allow_html=True)
    if warning_count:
        st.markdown(f'<div class="alert-warning">⚠️ {warning_count} قطعة في منطقة التحذير</div>',
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════
if page == "📊 لوحة التحكم":
    st.markdown("# 📊 لوحة تحكم المخزون")
    st.markdown(f"*آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    # ── KPI row ──────────────────────────────────────────────
    total_parts   = len(db["parts"])
    danger_parts  = sum(1 for p in db["parts"] if stock_status(p["current_stock"], p["danger_zone"]) == "danger")
    warning_parts = sum(1 for p in db["parts"] if stock_status(p["current_stock"], p["danger_zone"]) == "warning")
    ok_parts      = total_parts - danger_parts - warning_parts
    total_logs    = len(db["daily_logs"])

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">إجمالي القطع</div>'
                f'<div class="kpi-value">{total_parts}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card danger"><div class="kpi-label">🚨 منطقة خطر</div>'
                f'<div class="kpi-value" style="color:#dc2626">{danger_parts}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card warning"><div class="kpi-label">⚠️ منطقة تحذير</div>'
                f'<div class="kpi-value" style="color:#f59e0b">{warning_parts}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card success"><div class="kpi-label">✅ وضع آمن</div>'
                f'<div class="kpi-value" style="color:#16a34a">{ok_parts}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # ── Inventory bar chart ──────────────────────────────────
    st.markdown('<div class="section-header">📈 مستوى المخزون مقارنة بمنطقة الخطر</div>',
                unsafe_allow_html=True)

    chart_data = []
    for p in db["parts"]:
        product = get_product(db, next(
            b["product_id"] for b in db["bom"] if b["part_id"] == p["id"]
        ))
        status = stock_status(p["current_stock"], p["danger_zone"])
        color = {"danger": "#dc2626", "warning": "#f59e0b", "ok": "#16a34a"}[status]
        chart_data.append({
            "القطعة": p["name_ar"],
            "المخزون الحالي": max(p["current_stock"], 0),
            "منطقة الخطر": p["danger_zone"],
            "المنتج": product["name_ar"] if product else "—",
            "اللون": color,
        })

    df_chart = pd.DataFrame(chart_data)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="المخزون الحالي",
        x=df_chart["القطعة"],
        y=df_chart["المخزون الحالي"],
        marker_color=df_chart["اللون"],
        text=df_chart["المخزون الحالي"],
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        name="منطقة الخطر",
        x=df_chart["القطعة"],
        y=df_chart["منطقة الخطر"],
        mode="lines+markers",
        line=dict(color="#1e3a5f", width=2, dash="dash"),
        marker=dict(symbol="line-ew", size=10),
    ))
    fig.update_layout(
        barmode="group",
        height=420,
        font=dict(family="Cairo"),
        legend=dict(orientation="h", y=1.1),
        xaxis_tickangle=-35,
        margin=dict(t=40, b=80),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Active Alerts ────────────────────────────────────────
    st.markdown('<div class="section-header">🚨 التنبيهات النشطة</div>', unsafe_allow_html=True)
    any_alert = False
    for p in db["parts"]:
        status = stock_status(p["current_stock"], p["danger_zone"])
        if status == "danger":
            any_alert = True
            st.markdown(
                f'<div class="alert-danger">🚨 <b>{p["name_ar"]}</b> — '
                f'المخزون: <b>{p["current_stock"]}</b> وحدة | '
                f'منطقة الخطر: {p["danger_zone"]} وحدة</div>',
                unsafe_allow_html=True)
        elif status == "warning":
            any_alert = True
            st.markdown(
                f'<div class="alert-warning">⚠️ <b>{p["name_ar"]}</b> — '
                f'المخزون: <b>{p["current_stock"]}</b> وحدة | '
                f'منطقة الخطر: {p["danger_zone"]} وحدة</div>',
                unsafe_allow_html=True)
    if not any_alert:
        st.markdown('<div class="alert-ok">✅ جميع القطع في الوضع الآمن</div>', unsafe_allow_html=True)

    # ── Recent production log ────────────────────────────────
    if db["daily_logs"]:
        st.markdown('<div class="section-header">📋 آخر عمليات الإنتاج</div>', unsafe_allow_html=True)
        recent = db["daily_logs"][-5:][::-1]
        rows = []
        for log in recent:
            rows.append({
                "التاريخ": log["date"],
                "المنتج": log["product_name"],
                "الكمية المنتجة": log["qty_produced"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# PAGE: OCR UPLOAD
# ═══════════════════════════════════════════════════════════════
elif page == "📷 رفع تقرير الإنتاج":
    st.markdown("# 📷 رفع تقرير الإنتاج اليومي")
    st.info("ارفع صورة أو PDF لتقرير الإنتاج اليومي وسيقوم النظام تلقائيًا بقراءة الكميات وتحديث المخزون.")

    uploaded = st.file_uploader(
        "اختر صورة أو PDF للتقرير",
        type=["png", "jpg", "jpeg", "pdf"],
        help="يدعم النظام صيغ PNG, JPG, JPEG, PDF"
    )

    log_date = st.date_input("تاريخ التقرير", value=date.today())

    if uploaded:
        mime_map = {
            "png": "image/png", "jpg": "image/jpeg",
            "jpeg": "image/jpeg", "pdf": "application/pdf"
        }
        ext = uploaded.name.split(".")[-1].lower()
        mime = mime_map.get(ext, "image/jpeg")

        col_img, col_result = st.columns([1, 1])

        with col_img:
            st.markdown("**معاينة التقرير:**")
            if ext != "pdf":
                st.image(uploaded, use_container_width=True)
            else:
                st.info("📄 تم رفع ملف PDF")

        if st.button("🔍 تحليل التقرير باستخدام الذكاء الاصطناعي", type="primary"):
            with st.spinner("جارٍ قراءة التقرير... يرجى الانتظار"):
                try:
                    image_bytes = uploaded.read()
                    results = ocr_production_report(image_bytes, mime, db)

                    with col_result:
                        if not results:
                            st.warning("لم يتمكن النظام من قراءة أي بيانات من التقرير.")
                        else:
                            st.markdown("**النتائج المستخرجة من التقرير:**")
                            for r in results:
                                st.markdown(
                                    f'<div class="alert-ok">✅ <b>{r["product_name"]}</b>'
                                    f' — الكمية: <b>{r["qty_produced"]}</b> وحدة</div>',
                                    unsafe_allow_html=True)

                            if st.button("✅ تطبيق وتحديث المخزون", key="apply_ocr"):
                                for r in results:
                                    result = apply_production(
                                        db, r["product_id"],
                                        r["qty_produced"],
                                        str(log_date)
                                    )
                                    if result["success"]:
                                        st.success(f"تم خصم مكونات {r['product_name']} ✔")
                                        if result["alerts"]:
                                            st.warning(f"⚠️ تنبيه: {', '.join(result['alerts'])} وصلت لمنطقة الخطر!")
                                st.rerun()

                except json.JSONDecodeError:
                    st.error("خطأ في قراءة البيانات من الذكاء الاصطناعي. يرجى المحاولة مجددًا.")
                except Exception as e:
                    st.error(f"خطأ: {e}")


# ═══════════════════════════════════════════════════════════════
# PAGE: MANUAL ENTRY
# ═══════════════════════════════════════════════════════════════
elif page == "✏️ إدخال يدوي":
    st.markdown("# ✏️ إدخال الإنتاج اليومي يدويًا")

    col1, col2 = st.columns(2)
    with col1:
        product_options = {p["name_ar"]: p["id"] for p in db["products"]}
        selected_product_name = st.selectbox("اختر المنتج", list(product_options.keys()))
        selected_product_id = product_options[selected_product_name]

    with col2:
        qty = st.number_input("الكمية المنتجة", min_value=1, max_value=10000, value=10, step=1)

    entry_date = st.date_input("تاريخ الإنتاج", value=date.today())

    # Preview BOM impact before applying
    st.markdown('<div class="section-header">📋 تأثير الإنتاج على المكونات</div>', unsafe_allow_html=True)
    bom_rows = get_bom(db, selected_product_id)
    preview_data = []
    for row in bom_rows:
        part = get_part(db, row["part_id"])
        if part:
            deduct = row["qty_per_unit"] * qty
            new_stock = part["current_stock"] - deduct
            status = stock_status(new_stock, part["danger_zone"])
            preview_data.append({
                "المكون": part["name_ar"],
                "المخزون الحالي": part["current_stock"],
                "الخصم": deduct,
                "المخزون بعد الخصم": new_stock,
                "منطقة الخطر": part["danger_zone"],
                "الحالة": {"danger": "🚨 خطر", "warning": "⚠️ تحذير", "ok": "✅ آمن"}[status],
            })

    df_preview = pd.DataFrame(preview_data)
    st.dataframe(df_preview, use_container_width=True, hide_index=True)

    if st.button("✅ تأكيد وتطبيق الخصم", type="primary"):
        result = apply_production(db, selected_product_id, qty, str(entry_date))
        if result["success"]:
            st.success(f"✅ تم تسجيل إنتاج {qty} وحدة من {selected_product_name}")
            if result["alerts"]:
                st.error(f"🚨 تحذير: القطع التالية وصلت لمنطقة الخطر:\n" + "\n".join(result["alerts"]))
            st.rerun()
        else:
            st.error(result["error"])


# ═══════════════════════════════════════════════════════════════
# PAGE: INVENTORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════
elif page == "📦 إدارة المخزون":
    st.markdown("# 📦 إدارة المخزون الحالي")

    # Filter by product
    filter_product = st.selectbox(
        "تصفية حسب المنتج",
        ["الكل"] + [p["name_ar"] for p in db["products"]]
    )

    for product in db["products"]:
        if filter_product != "الكل" and product["name_ar"] != filter_product:
            continue

        st.markdown(f'<div class="section-header">🪑 {product["name_ar"]}</div>', unsafe_allow_html=True)

        bom_rows = get_bom(db, product["id"])
        rows = []
        for row in bom_rows:
            part = get_part(db, row["part_id"])
            if not part:
                continue
            status = stock_status(part["current_stock"], part["danger_zone"])
            rows.append({
                "المكون": part["name_ar"],
                "معدل السحب": row["qty_per_unit"],
                "المخزون الحالي": part["current_stock"],
                "منطقة الخطر": part["danger_zone"],
                "الحالة": {"danger": "🚨 خطر", "warning": "⚠️ تحذير", "ok": "✅ آمن"}[status],
                "part_id": part["id"],
            })

        # Editable stock adjustment
        for i, row_data in enumerate(rows):
            with st.expander(f"{row_data['الحالة']} {row_data['المكون']} — مخزون: {row_data['المخزون الحالي']}"):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    new_stock = st.number_input(
                        "تعديل المخزون", value=row_data["المخزون الحالي"],
                        key=f"stock_{row_data['part_id']}", step=10
                    )
                with col_b:
                    new_danger = st.number_input(
                        "منطقة الخطر", value=row_data["منطقة الخطر"],
                        key=f"danger_{row_data['part_id']}", step=50
                    )
                with col_c:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 حفظ", key=f"save_{row_data['part_id']}"):
                        part = get_part(db, row_data["part_id"])
                        part["current_stock"] = new_stock
                        part["danger_zone"] = new_danger
                        save_db(db)
                        st.success("تم الحفظ ✔")
                        st.rerun()

        # Stock replenishment
        st.markdown("**إضافة مخزون (استلام شحنة):**")
        col_p, col_q, col_add = st.columns(3)
        part_options = {get_part(db, r["part_id"])["name_ar"]: r["part_id"] for r in bom_rows}
        with col_p:
            restock_part_name = st.selectbox("القطعة", list(part_options.keys()),
                                              key=f"restock_part_{product['id']}")
        with col_q:
            restock_qty = st.number_input("الكمية المضافة", min_value=1, value=100,
                                          key=f"restock_qty_{product['id']}")
        with col_add:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ إضافة للمخزون", key=f"restock_btn_{product['id']}"):
                part = get_part(db, part_options[restock_part_name])
                part["current_stock"] += restock_qty
                save_db(db)
                st.success(f"تمت إضافة {restock_qty} وحدة لـ {restock_part_name} ✔")
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# PAGE: DAILY LOGS
# ═══════════════════════════════════════════════════════════════
elif page == "📋 سجل العمليات":
    st.markdown("# 📋 سجل عمليات الإنتاج")

    if not db["daily_logs"]:
        st.info("لا توجد سجلات بعد. قم بتسجيل أول دفعة إنتاج.")
    else:
        logs = db["daily_logs"][::-1]  # Newest first
        summary_rows = []
        for log in logs:
            summary_rows.append({
                "التاريخ": log["date"],
                "المنتج": log["product_name"],
                "الكمية المنتجة": log["qty_produced"],
                "عدد المكونات المخصومة": len(log["deductions"]),
            })

        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        # Detailed log viewer
        st.markdown('<div class="section-header">تفاصيل السجل</div>', unsafe_allow_html=True)
        log_index = st.number_input("رقم السجل (من الأحدث)", min_value=1,
                                    max_value=len(logs), value=1, step=1)
        log = logs[log_index - 1]

        st.markdown(f"**التاريخ:** {log['date']} | **المنتج:** {log['product_name']} | "
                    f"**الكمية:** {log['qty_produced']} وحدة")

        deduction_rows = []
        for d in log["deductions"]:
            deduction_rows.append({
                "المكون": d["part_name"],
                "الكمية المخصومة": d["deducted"],
                "المخزون المتبقي": d["remaining"],
                "منطقة الخطر": d["danger_zone"],
                "الحالة": {"danger": "🚨 خطر", "warning": "⚠️ تحذير", "ok": "✅ آمن"}[d["status"]],
            })
        st.dataframe(pd.DataFrame(deduction_rows), use_container_width=True, hide_index=True)

        # Export CSV
        csv = pd.DataFrame(summary_rows).to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تصدير السجل CSV", csv, "production_log.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════
elif page == "⚙️ إعدادات المنتجات":
    st.markdown("# ⚙️ إعدادات المنتجات والمكونات")

    tab1, tab2 = st.tabs(["📋 قائمة المكونات", "➕ إضافة منتج / مكون"])

    with tab1:
        st.markdown("**جميع المكونات في قاعدة البيانات:**")
        all_parts = []
        for p in db["parts"]:
            product_id = next(
                (b["product_id"] for b in db["bom"] if b["part_id"] == p["id"]), "—"
            )
            product = get_product(db, product_id)
            bom_row = next((b for b in db["bom"] if b["part_id"] == p["id"]), {})
            all_parts.append({
                "المعرف": p["id"],
                "اسم المكون": p["name_ar"],
                "المنتج الرئيسي": product["name_ar"] if product else "—",
                "معدل السحب": bom_row.get("qty_per_unit", "—"),
                "المخزون الحالي": p["current_stock"],
                "منطقة الخطر": p["danger_zone"],
            })
        st.dataframe(pd.DataFrame(all_parts), use_container_width=True, hide_index=True)

        # Reset button
        if st.button("🔄 إعادة تعيين قاعدة البيانات للقيم الافتراضية", type="secondary"):
            if st.session_state.get("confirm_reset"):
                db = build_default_db()
                save_db(db)
                st.session_state.db = db
                st.session_state.confirm_reset = False
                st.success("تمت إعادة التعيين ✔")
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("اضغط مرة أخرى للتأكيد.")

    with tab2:
        st.markdown("**إضافة مكون جديد:**")
        col1, col2 = st.columns(2)
        with col1:
            new_part_name = st.text_input("اسم المكون (عربي)")
            new_part_name_en = st.text_input("اسم المكون (إنجليزي)")
            new_stock = st.number_input("المخزون الابتدائي", min_value=0, value=100)
        with col2:
            new_danger = st.number_input("منطقة الخطر", min_value=0, value=200)
            product_for_new = st.selectbox("المنتج الرئيسي",
                                           [p["name_ar"] for p in db["products"]])
            qty_per_unit = st.number_input("معدل السحب (qty per chair)", min_value=1, value=1)

        if st.button("➕ إضافة المكون", type="primary"):
            if new_part_name:
                new_id = f"S{len(db['parts']) + 1:03d}"
                product_id = next(p["id"] for p in db["products"] if p["name_ar"] == product_for_new)
                db["parts"].append({
                    "id": new_id, "name_ar": new_part_name, "name_en": new_part_name_en,
                    "product_id": product_id, "current_stock": new_stock,
                    "danger_zone": new_danger, "unit": "pcs"
                })
                db["bom"].append({
                    "product_id": product_id, "part_id": new_id, "qty_per_unit": qty_per_unit
                })
                save_db(db)
                st.success(f"تمت إضافة '{new_part_name}' بنجاح ✔")
                st.rerun()
            else:
                st.warning("يرجى إدخال اسم المكون.")
