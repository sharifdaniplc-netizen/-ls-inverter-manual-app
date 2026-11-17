import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os

# --- تنظیمات اولیه صفحه ---
st.set_page_config(page_title="LS Inverter SV-iG5A Manual Viewer", layout="wide")

# --- استایل سفارشی برای بهبود ظاهر ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
    }
    .stExpander {
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- بارگذاری فایل PDF ---
PDF_PATH = "LS_Inverter_SV-IG5A_Series_User_Manual.pdf"

@st.cache_resource
def load_pdf(path):
    if os.path.exists(path):
        return fitz.open(path)
    return None

doc = load_pdf(PDF_PATH)

if doc is None:
    st.error(f"خطا: فایل PDF یافت نشد! مطمئن شوید فایل '{PDF_PATH}' در کنار این فایل قرار دارد.")
    st.stop()

# --- مدیریت وضعیت (Session State) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# --- توابع کمکی ---
def get_page_image(page_num, zoom=1.5):
    page = doc.load_page(page_num)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    return Image.open(io.BytesIO(img_data))

# --- نوار کناری (Sidebar) برای کنترل‌ها ---
with st.sidebar:
    st.title("🛠 Controls")
    
    # پیمایش صفحات
    st.subheader("📄 Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Previous"):
            if st.session_state.current_page > 0:
                st.session_state.current_page -= 1
                st.rerun()
    with col2:
        if st.button("Next ➡️"):
            if st.session_state.current_page < len(doc) - 1:
                st.session_state.current_page += 1
                st.rerun()
    
    st.write(f"**Page:** {st.session_state.current_page + 1} / {len(doc)}")
    
    # زوم
    zoom_level = st.slider("🔍 Zoom Level", 1.0, 3.0, 1.5, 0.1)

    st.divider()

    # بخش جستجو
    st.subheader("🔍 Search")
    search_query = st.text_input("Enter keyword...")
    if st.button("Search"):
        results = []
        for i in range(len(doc)):
            text = doc[i].get_text().lower()
            if search_query.lower() in text:
                results.append(i)
        st.session_state.search_results = results
        if results:
            st.success(f"Found {len(results)} matches!")
        else:
            st.warning("No results found.")

    st.divider()

    # بخش کدهای خطا (Fault Codes)
    st.subheader("⚠️ Fault Codes")
    fault_map = {
        "OC": 162, "OV": 162, "LV": 162, "OHT": 162,
        "GFT": 162, "IOLT": 167, "OLT": 144, "EEP": 163, "HWT": 163
    }
    selected_fault = st.selectbox("Select Fault:", ["None"] + list(fault_map.keys()))
    if selected_fault != "None":
        if st.button(f"Go to {selected_fault}"):
            st.session_state.current_page = fault_map[selected_fault]
            st.rerun()

    st.divider()

    # بخش بوک‌مارک‌ها
    st.subheader("🔖 Bookmarks")
    if st.button("➕ Add Current Page"):
        if st.session_state.current_page not in st.session_state.bookmarks:
            st.session_state.bookmarks.append(st.session_state.current_page)
            st.rerun()
    
    for idx, bm_page in enumerate(st.session_state.bookmarks):
        if st.button(f"Page {bm_page + 1}", key=f"bm_{idx}"):
            st.session_state.current_page = bm_page
            st.rerun()

# --- بخش اصلی (Main Area) ---
st.title("📖 LS Inverter SV-iG5A Manual")

# نمایش نتایج جستجو اگر وجود داشته باشد
if st.session_state.search_results:
    with st.expander("🔍 Search Results (Click to jump)"):
        for res_page in st.session_state.search_results:
            if st.button(f"Go to Page {res_page + 1}", key=f"res_{res_page}"):
                st.session_state.current_page = res_page
                st.rerun()

# نمایش صفحه PDF
try:
    page_img = get_page_image(st.session_state.current_page, zoom=zoom_level)
    st.image(page_img, use_container_width=True)
except Exception as e:
    st.error(f"Error rendering page: {e}")

# نمایش فهرست مطالب (Contents) در انتهای صفحه
with st.expander("📂 Table of Contents"):
    toc = doc.get_toc()
    for entry in toc:
        # entry format: [level, title, page]
        level, title, page_num = entry
        if st.button(f"{'  ' * (level-1)}• {title}", key=f"toc_{page_num}_{title[:10]}"):
            st.session_state.current_page = page_num - 1
            st.rerun()
