import streamlit as st
import google.generativeai as genai
import os
import base64
import time
import smtplib
import json
import csv
import random
import re
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import Counter
from gtts import gTTS

# --- 1. CONFIG & SESSION ---
st.set_page_config(page_title="Trợ lý của Sinh viên K17", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "ratings" not in st.session_state:
    st.session_state.ratings = {}
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "📍 Chế độ Tra cứu (Nghiêm ngặt)"
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

# --- USER NAME GATE ---
if "user_name" not in st.session_state:
    st.markdown("<div style='background:rgba(255,255,255,0.05); padding:30px; border-radius:20px; text-align:center; margin-top:50px;'><h2 style='color:#a78bfa;'>👋 Chào mừng bạn đến với Trợ lý K17!</h2><p style='color:#94a3b8;'>Để bắt đầu cuộc trò chuyện, vui lòng cho mình biết tên của bạn:</p></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input("Tên của bạn:", key="gate_name", placeholder="Ví dụ: Nguyễn Văn A")
        if st.button("🚀 Bắt đầu ngay", use_container_width=True):
            if name.strip():
                st.session_state.user_name = name.strip()
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập tên!")
    st.stop()

# --- 2. API KEYS ---
try:
    API_KEYS = st.secrets.get("GEMINI_API_KEYS", [])
except Exception:
    API_KEYS = []

if not API_KEYS:
    # PHÒNG NGỪA RÒ RỈ (Repo Công khai): Tuyệt đối không dán mã API thật vào đây.
    # Hãy dán mã API vào mục Secrets trên Streamlit Cloud hoặc file secrets.toml cục bộ.
    API_KEYS = [] 

VALID_KEYS = [k for k in API_KEYS if k and "VUI_LONG" not in k]

if not VALID_KEYS:
    st.error("❌ Lỗi bảo mật: Không tìm thấy API Key trong hệ thống Secrets!")
    st.info("💡 Hướng dẫn cho Admin: Vui lòng kiểm tra và dán API Key hợp lệ vào mục Secrets trên Streamlit Cloud hoặc file secrets.toml cục bộ để kích hoạt ứng dụng.")
    st.stop()

def configure_genai(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-flash-latest')

# --- 3. UI LOCALIZATION ---
UI_LANG = {
    "vi": {
        "analyzing": "🧠 Chuyên gia AI đang phân tích...",
        "scanning": "🔍 Đang quét tri thức Handbook & Skills...",
        "scanning_std": "🔍 Đang quét tri thức Handbook & Standards...",
        "finalizing": "✅ Hoàn tất!",
        "writing": "✍️ Đang soạn câu trả lời...",
        "source": "📖 Cơ sở văn bản",
        "verify": "🔍 Đối chiếu văn bản gốc",
        "back": "⬅️ Quay lại Công cụ",
        "view_source_hint": "Bấm vào các nút dưới đây để đối chiếu từng nguồn:",
        "verified_hint": "💡 Đây là đoạn văn bản gốc mà AI đã trích dẫn để đưa ra câu trả lời.",
        "suggest_title": "💡 Gợi ý cho bạn:"
    },
    "en": {
        "analyzing": "🧠 AI Expert is analyzing...",
        "scanning": "🔍 Scanning Handbook & Skills knowledge...",
        "scanning_std": "🔍 Scanning Handbook & Standards knowledge...",
        "finalizing": "✅ Completed!",
        "writing": "✍️ Drafting response...",
        "source": "📖 Source Information",
        "verify": "🔍 Verify Source Text",
        "back": "⬅️ Back to Tools",
        "view_source_hint": "Click the buttons below to verify each source:",
        "verified_hint": "💡 This is the original text cited by the AI for its response.",
        "suggest_title": "💡 Suggestions for you:"
    }
}

def detect_language(text):
    vi_chars = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    if any(c in vi_chars for c in text.lower()):
        return "vi"
    vi_words = {"hoc", "sinh", "vien", "nganh", "nghe", "tot", "nghiep", "dang", "ky", "tin", "chi", "truong", "co", "va", "nhung", "la", "cua", "trong", "cho", "duoc", "nguoi", "khong", "phai", "nao", "dau", "sao", "nay", "thi", "lam"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if words.intersection(vi_words):
        return "vi"
    return "en"

# --- 4. HELPERS ---
def parse_citations(text):
    if "---TRÍCH DẪN NGUỒN---" not in text:
        return {}
    parts = text.split("---TRÍCH DẪN NGUỒN---")
    source_section = parts[1].strip()
    pattern = r"\[(\d+)\](.*?)(?=\s*\[\d+\]|$)"
    matches = re.findall(pattern, source_section, re.DOTALL)
    return {num: content.strip() for num, content in matches}

def load_knowledge_base(include_skills=False, include_standards=False, query=""):
    knowledge = ""
    files = ["huong-dan.txt", "QTNNL-handbook.md"]
    for filename in files:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
                knowledge += f"\n--- NỘI DUNG HANDBOOK ({filename}) ---\n" + content
    if include_skills:
        skills_dir = "claude-skills"
        domain_map = {
            "c-level-advisor/chro-advisor": ["lương", "tuyển dụng", "định biên", "nhân sự", "hr", "compensation", "hiring"],
            "c-level-advisor/culture-architect": ["văn hóa", "môi trường", "gắn kết", "giá trị", "culture", "engagement"],
            "c-level-advisor/executive-mentor": ["kỹ năng", "lãnh đạo", "nghề nghiệp", "phát triển", "mentor", "leadership", "career"],
            "project-management": ["dự án", "nhóm", "kế hoạch", "tiến độ", "project", "planning"]
        }
        q_lower = query.lower()
        selected_domains = [domain for domain, keywords in domain_map.items() if any(kw in q_lower for kw in keywords)]
        if not selected_domains:
            selected_domains = ["c-level-advisor/chro-advisor", "c-level-advisor/culture-architect", "c-level-advisor/executive-mentor"]
        for domain in selected_domains:
            skill_file = os.path.join(skills_dir, domain, "SKILL.md")
            if os.path.exists(skill_file):
                try:
                    with open(skill_file, "r", encoding="utf-8") as f:
                        knowledge += f"\n\n--- TRI THỨC CHUYÊN GIA: {domain.upper()} ---\n" + f.read()
                except:
                    continue
    if include_standards and not include_skills:
        std_path = "claude-skills/standards/documentation/documentation-standards.md"
        if os.path.exists(std_path):
            with open(std_path, "r", encoding="utf-8") as f:
                knowledge += f"\n\n--- TIÊU CHUẨN TRÌNH BÀY VĂN BẢN ---\n" + f.read()
    return knowledge

# ===== CẤU HÌNH GMAIL =====
SENDER_EMAIL = "leedanh2005@gmail.com"
SENDER_PASSWORD = "bgoa ftww iqvr xqap"

def send_email(to_email, chat_history):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "📚 Lịch sử hội thoại - Trợ lý Sinh viên K17"
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        user_name = st.session_state.get('user_name', 'người dùng')
        body = f"Dưới đây là nội dung hội thoại của {user_name} với Trợ lý K17:\n\n"
        body += "=" * 50 + "\n\n"
        for m in chat_history:
            role = "🧑 Bạn" if m["role"] == "user" else "🤖 Trợ lý"
            body += f"{role}:\n{m['content']}\n\n"
            body += "-" * 40 + "\n\n"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        return str(e)

# ===== LOGS =====
def save_to_log(q, a, d=None):
    log_f = "chat_log.json"
    logs = []
    if os.path.exists(log_f):
        with open(log_f, "r", encoding="utf-8") as f:
            logs = json.load(f)
    logs.append({"thoi_gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "cau_hoi": q, "cau_tra_loi": a, "danh_gia": d})
    with open(log_f, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def save_to_csv(user_name, question, answer):
    try:
        csv_f = os.path.join(os.getcwd(), "chat_history.csv")
        exist = os.path.isfile(csv_f)
        with open(csv_f, mode='a', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            if not exist:
                w.writerow(["Thời gian", "Tên người dùng", "Câu hỏi", "Câu trả lời"])
            w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_name, question, answer])
        return True
    except Exception:
        return False

def update_rating_in_log(idx, d):
    log_f = "chat_log.json"
    if not os.path.exists(log_f): return
    with open(log_f, "r", encoding="utf-8") as f:
        logs = json.load(f)
    if idx < len(logs):
        logs[idx]["danh_gia"] = d
        with open(log_f, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

def speak(text, lang='vi'):
    try:
        clean_text = re.sub(r'\[\d+\]', '', text)
        tts = gTTS(text=clean_text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception:
        return None

def get_base64_image(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

def highlight_keywords(text):
    if "```mermaid" in text: return text
    for kw in ["tín chỉ", "tốt nghiệp", "thực tập", "chuẩn đầu ra", "học phần"]:
        text = text.replace(kw, f"**{kw}**").replace(kw.capitalize(), f"**{kw.capitalize()}**")
    return text

# --- 5. DASHBOARD ---
def show_admin_dashboard():
    st.markdown("<h2 style='color: #a78bfa;'>📊 Nhịp đập Nhân sự K17</h2>", unsafe_allow_html=True)
    try:
        df = pd.read_csv("chat_history.csv")
        with open("chat_log.json", "r", encoding="utf-8") as f:
            logs = json.load(f)
    except:
        st.warning("Chưa có đủ dữ liệu để thống kê.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🔍 Phân loại chủ đề")
        keywords = {
            "Học tập": ["tín chỉ", "tốt nghiệp", "học phần", "điểm", "gpa", "lịch thi"],
            "Nghề nghiệp": ["tuyển dụng", "cv", "phỏng vấn", "lương", "thù lao", "career"],
            "Kỹ năng": ["lãnh đạo", "giao tiếp", "đàm phán", "mentor", "kỹ năng"],
            "Thực tập": ["thực tập", "doanh nghiệp", "báo cáo", "kiến tập"]
        }
        counts = Counter()
        for q in df["Câu hỏi"].dropna():
            found = False
            for cat, kws in keywords.items():
                if any(kw in q.lower() for kw in kws):
                    counts[cat] += 1
                    found = True
            if not found: counts["Khác"] += 1
        fig_pie = px.pie(values=list(counts.values()), names=list(counts.keys()), 
                         color_discrete_sequence=px.colors.sequential.RdBu, hole=0.4)
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.markdown("### ⭐ Độ hài lòng")
        pos = sum(1 for l in logs if l.get("danh_gia") == "👍")
        neg = sum(1 for l in logs if l.get("danh_gia") == "👎")
        total = pos + neg
        rate = (pos / total * 100) if total > 0 else 100
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = rate,
            title = {'text': "Tỉ lệ hài lòng (%)"},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#a78bfa"}}))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("### 📈 Từ khóa đang Hot")
    all_text = " ".join(df["Câu hỏi"].dropna().astype(str)).lower()
    words = re.findall(r'\b\w{4,}\b', all_text)
    stop_words = ["mình", "của", "cho", "được", "trong", "là", "và", "có", "không", "nào", "phải", "như", "này", "thế"]
    filtered_words = [w for w in words if w not in stop_words]
    top_words = Counter(filtered_words).most_common(10)
    word_df = pd.DataFrame(top_words, columns=['Word', 'Count'])
    fig_bar = px.bar(word_df, x='Count', y='Word', orientation='h', color='Count', color_continuous_scale='Purples')
    fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_bar, use_container_width=True)
    st.divider()
    active_keys = len([k for k in VALID_KEYS if k])
    st.markdown(f"📡 **Hệ thống:** Đang bảo vệ bởi `{active_keys}` Lõi năng lượng. Tình trạng: `Ổn định`.")

# --- CSS & HEADER ---
is_con_ui = "Tư vấn" in st.session_state.chat_mode
if is_con_ui:
    bg_gradient = "radial-gradient(circle at top right, #581c87, #020617), radial-gradient(circle at bottom left, #431407, #020617)"
else:
    bg_gradient = "radial-gradient(circle at top right, #0c4a6e, #020617), radial-gradient(circle at bottom left, #1e1b4b, #020617)"

st.markdown(f"""<style>
html, body, .stApp {{ background: {bg_gradient}; background-attachment: fixed; color: #f1f5f9; }}
[data-testid="stSidebar"] {{ background: rgba(2, 6, 23, 0.5) !important; backdrop-filter: blur(40px) saturate(150%); border-right: 1px solid rgba(255, 255, 255, 0.05); }}
.header-container {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); padding: 25px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.05); }}
[data-testid="stChatMessage"] > div {{ border-radius: 24px !important; padding: 20px 25px !important; margin-bottom: 12px !important; }}
.action-btn {{ background: transparent !important; border: none !important; color: white !important; font-size: 18px !important; cursor: pointer; }}
.status-text {{ font-size: 12px; color: #a78bfa; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}
.progress-container {{ background: rgba(255, 255, 255, 0.05); height: 6px; border-radius: 10px; overflow: hidden; margin-bottom: 8px; }}
.progress-bar {{ background: linear-gradient(90deg, #a78bfa, #38bdf8, #a78bfa); background-size: 200% 100%; height: 100%; transition: width 0.5s; animation: shimmer 2s infinite linear; }}
@keyframes shimmer {{ 0% {{ background-position: 200% 0; }} 100% {{ background-position: -200% 0; }} }}
.thinking-wave {{ display: flex; gap: 3px; margin-bottom: 20px; }}
.thinking-wave div {{ width: 4px; height: 12px; background: #a78bfa; border-radius: 2px; animation: wave-pulse 1s infinite ease-in-out; }}
.thinking-wave div:nth-child(2) {{ animation-delay: 0.1s; }}
.thinking-wave div:nth-child(3) {{ animation-delay: 0.2s; }}
.thinking-wave div:nth-child(4) {{ animation-delay: 0.3s; }}
@keyframes wave-pulse {{ 0%, 100% {{ height: 8px; opacity: 0.5; }} 50% {{ height: 18px; opacity: 1; background: #38bdf8; }} }}
@keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});</script>""", unsafe_allow_html=True)

# --- HEADER LOGIC ---
if not st.session_state.admin_mode:
    if os.path.exists("background_due.jpg"):
        img_b64 = get_base64_image("background_due.jpg")
        st.markdown(f'<div class="header-container" style="display:flex; align-items:center;"><div style="margin-right:20px;"><img src="data:image/jpg;base64,{img_b64}" style="border-radius:14px; width:60px; height:60px; object-fit:cover;"/></div><div><h1 style="margin:0; font-size:22px; font-weight:800;">🎓 <span style="background:linear-gradient(90deg,#a78bfa,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Trợ lý Sinh viên K17</span></h1><p style="margin:0; color:#94a3b8; font-size:12px;">Intelligent Assistant Portal</p></div></div>', unsafe_allow_html=True)
    else:
        st.title("🎓 Trợ lý Sinh viên K17")

# --- SIDEBAR ---
with st.sidebar:
    if st.session_state.get("view_cited_text"):
        cited = st.session_state.view_cited_text
        lang = st.session_state.get("last_lang", "vi")
        if st.button(UI_LANG[lang]["back"], use_container_width=True):
            st.session_state.view_cited_text = None
            st.rerun()
        st.markdown(f"### {UI_LANG[lang]['verify']}")
        st.markdown(f'<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border-left:4px solid #a78bfa; color:#cbd5e1;">{cited}</div>', unsafe_allow_html=True)
        st.info(UI_LANG[lang]["verified_hint"])
    else:
        st.markdown("<h2 style='text-align: center; color: #a78bfa; font-weight:800;'>🚀 CÔNG CỤ</h2>", unsafe_allow_html=True)
        st.markdown("### 🔍 Tra cứu sổ tay")
        sq = st.text_input("Từ khóa:", key="sb_search", placeholder="Gõ để tìm...")
        if sq and os.path.exists("QTNNL-handbook.md"):
            with open("QTNNL-handbook.md", "r", encoding="utf-8") as f: content = f.read()
            results = [s for s in content.split("##") if sq.lower() in s.lower()]
            for r in results[:3]:
                with st.expander(f"📖 {r.strip().splitlines()[0][:30]}..."): st.markdown(r)
        st.divider(); st.markdown("### 🔗 Links")
        c1, c2 = st.columns(2)
        with c1: st.link_button("🌐 Web", "https://due.udn.vn/"); st.link_button("📊 Điểm", "http://daotao.due.udn.vn/")
        with c2: st.link_button("📚 HR", "https://sites.google.com/view/quantringuonnhanluc"); st.link_button("🏢 QTKD", "https://due.udn.vn/vi-vn/khoa/quan-tri-kinh-doanh")
        st.divider()
        if st.button("🗑️ Xóa lịch sử", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Admin Login
        if not st.session_state.admin_mode:
            with st.expander("🛠️ Quản trị hệ thống"):
                ad_pw = st.text_input("Mật khẩu Admin:", type="password")
                if st.button("Truy cập Dashboard", use_container_width=True):
                    if ad_pw == "0913":
                        st.session_state.admin_mode = True
                        st.rerun()
                    else: st.error("Sai mật khẩu!")
        else:
            if st.button("⬅️ Quay lại Chat", use_container_width=True):
                st.session_state.admin_mode = False
                st.rerun()

        with st.expander("✉️ Gửi lịch sử hội thoại"):
            em = st.text_input("Nhập Email của bạn:")
            if st.button("Gửi Mail", use_container_width=True):
                if em:
                    res = send_email(em, st.session_state.messages)
                    if res == True:
                        st.success("Đã gửi thành công!")
                    else:
                        st.error(f"Lỗi: {res}")

# --- JS COPY ---
st.markdown("""<script>function copyText(id){const el=document.getElementById(id);const t=el.innerText||el.textContent;navigator.clipboard.writeText(t).then(function(){const btn=document.getElementById('copybtn_'+id);btn.innerHTML='✅';setTimeout(function(){btn.innerHTML='📋';},2000);});}</script>""", unsafe_allow_html=True)

# --- MAIN PAGE ROUTING ---
if st.session_state.admin_mode:
    show_admin_dashboard()
else:
    # --- GREETING ---
    if not st.session_state.messages:
        loi_chao = """Chào các bạn, mình là AI Chatbot do sinh viên Lê Công Danh lớp Tuyển dụng 49K17.2 xây dựng nhằm đồng hành và cung cấp thông tin cho những học sinh đang quan tâm đến ngành Quản trị Nhân lực tại Trường Đại học Kinh tế – Đại học Đà Nẵng. Mình sẽ giúp các bạn tìm hiểu rõ hơn về ngành học, chương trình đào tạo và những nội dung liên quan trong quá trình lựa chọn.\n\n---\n💡 **HỖ TRỢ TỐT NHẤT CHO BẠN:**\n*   📍 **Chế độ Tra cứu:** Giải đáp chính xác 100% quy định từ Sổ tay sinh viên.\n*   🚀 **Chế độ Tư vấn:** Kích hoạt "Hội đồng chuyên gia HR" tư vấn chiến lược, nghề nghiệp và kỹ năng thực tế.\n*   📖 **Đối chiếu Nguồn:** Bấm số `[1]`, `[2]` để xem văn bản gốc (đôi khi tính năng này ẩn, hãy hỏi câu khác để khắc phục).\n*   🔊 **Giọng nói AI:** Bấm biểu tượng loa để nghe AI tư vấn với tốc độ cực nhanh.\n*   ➕ **Tính năng Nâng cao (vẫn đang trong quá trình phát triển):** Nhấn dấu cộng để tải lên Bảng điểm, CV (PDF/Ảnh) và yêu cầu AI phân tích sâu."""
        with st.chat_message("assistant"): st.markdown(loi_chao)

    # --- HISTORY ---
    assistant_idx = 0
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            parts = m["content"].split("---TRÍCH DẪN NGUỒN---")
            main_c = parts[0].strip(); st.markdown(highlight_keywords(main_c))
            if m["role"] == "assistant" and len(parts) > 1:
                with st.expander("📖 Cơ sở văn bản"):
                    cits = parse_citations(m["content"])
                    if cits:
                        cols = st.columns(len(cits) if len(cits) < 6 else 5)
                        for idx, (num, txt) in enumerate(cits.items()):
                            if cols[idx % 5].button(f"[{num}]", key=f"h_{i}_{num}"): st.session_state.view_cited_text = txt; st.rerun()
                    else: st.markdown(parts[1].strip())
            if m["role"] == "assistant":
                msg_id = f"msg_{assistant_idx}"; rating = st.session_state.ratings.get(msg_id)
                safe_c = main_c.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ')
                st.markdown('<div style="margin-top: -15px;"></div>', unsafe_allow_html=True)
                c1, c2, c3, c4, _ = st.columns([0.8, 0.8, 0.8, 0.8, 8.8])
                with c1: 
                    if st.button("👍" if rating != "👍" else "✅👍", key=f"lk_{msg_id}"): st.session_state.ratings[msg_id] = "👍"; update_rating_in_log(assistant_idx, "👍"); st.rerun()
                with c2:
                    if st.button("👎" if rating != "👎" else "✅👎", key=f"dl_{msg_id}"): st.session_state.ratings[msg_id] = "👎"; update_rating_in_log(assistant_idx, "👎"); st.rerun()
                with c3:
                    st.markdown(f'<span id="content_{msg_id}" style="display:none">{safe_c}</span><button class="action-btn" id="copybtn_content_{msg_id}" onclick="copyText(\'content_{msg_id}\')">📋</button>', unsafe_allow_html=True)
                with c4:
                    if st.button("🔊", key=f"tts_{msg_id}"):
                        lc = detect_language(m["content"]); aud = speak(main_c, lang=lc)
                        if aud: st.session_state[f"playing_{msg_id}"] = aud
                if f"playing_{msg_id}" in st.session_state: st.audio(st.session_state[f"playing_{msg_id}"], autoplay=True)
                assistant_idx += 1

    # --- INPUT ---
    with st.container():
        st.markdown("<p style='color: #94a3b8; font-size: 13px; font-weight: 500; margin-bottom: 5px;'>💡 GỢI Ý CHO BẠN:</p>", unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        if s1.button("🧭 Học phần Tuyển dụng có bao nhiêu tín", key="sug_1", use_container_width=True): st.session_state.suggested_prompt = "🧭 Cho mình biết học phần Tuyển dụng có bao nhiêu tín chỉ và nội dung chính của môn này là gì?"; st.rerun()
        if s2.button("🎓 Quy định tốt nghiệp", key="sug_2", use_container_width=True): st.session_state.suggested_prompt = "🎓 Những điều kiện quan trọng nhất để được xét tốt nghiệp ngành Quản trị nhân lực là gì?"; st.rerun()
        if s3.button("💰 Tốt nghiệp sớm được không?", key="sug_3", use_container_width=True): st.session_state.suggested_prompt = "💰 Mình có thể tốt nghiệp sớm được không? Điều kiện và lộ trình để ra trường sớm là gì?"; st.rerun()

        cp, ch, ci = st.columns([0.6, 3, 6])
        with cp:
            with st.popover("➕"):
                up = st.file_uploader("Tệp", type=['pdf','png','jpg'], key="file_up")
                mode = st.radio("Chế độ:", ["📍 Chế độ Tra cứu", "🚀 Chế độ Tư vấn"], index=0 if "Tra cứu" in st.session_state.chat_mode else 1)
                if mode != st.session_state.chat_mode: st.session_state.chat_mode = mode; st.rerun()
        with ch: 
            if not st.session_state.get("file_up"): st.markdown('<span style="color:#fb7185;font-weight:bold;font-size:13px;animation: blink 1s infinite;">⬅️ Tính năng nâng cao</span>', unsafe_allow_html=True)
        with ci: st.caption(f"Đang dùng: {st.session_state.chat_mode}")

    prompt = st.chat_input("Hỏi Trợ lý K17...")
    if st.session_state.get("suggested_prompt"):
        prompt = st.session_state.pop("suggested_prompt")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt}); st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        u_msg = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            prog_ph = st.empty()
            def up_p(t, w): prog_ph.markdown(f'<div class="status-text">{t}</div><div class="progress-container"><div class="progress-bar" style="width:{w}%"></div></div><div class="thinking-wave"><div></div><div></div><div></div><div></div></div>', unsafe_allow_html=True)
            is_con = "Tư vấn" in st.session_state.chat_mode; lang = detect_language(u_msg); st.session_state.last_lang = lang; ui = UI_LANG[lang]
            up_p(ui["scanning"], 20); ctx = load_knowledge_base(is_con, not is_con, query=u_msg)
            up_p(ui["analyzing"], 50)
            l_inst = ""
            if lang == "en": l_inst = "LANGUAGE REQUIREMENT: Respond 100% in English. Translate all knowledge from Handbook/Skills into professional English."
            if is_con: inst = f"(BẠN LÀ CHUYÊN GIA HR. {l_inst} Vận dụng Skills. Trực quan hóa bằng Mermaid nếu cần. Trích dẫn [n] nguyên văn. Cuối bài: ---TRÍCH DẪN NGUỒN--- [n] Câu văn (Nguồn))"
            else: inst = f"(BẠN LÀ TRỢ LÝ TRA CỨU. {l_inst} Chỉ Handbook. Trực quan hóa Mermaid nếu có quy trình. Trích dẫn [n] nguyên văn. Cuối bài: ---TRÍCH DẪN NGUỒN--- [n] Câu văn (Nguồn))"
            query = [f"Bối cảnh: {ctx}\n{inst}\n\nCâu hỏi: {u_msg}"]
            if st.session_state.get("file_up"):
                f = st.session_state.file_up; query.insert(0, {"mime_type": f.type, "data": f.read()})
            success = False; attempts = 0; keys = VALID_KEYS.copy(); random.shuffle(keys)
            while not success and attempts < len(keys):
                try:
                    up_p(f"{ui['writing']} (Key {attempts+1})", 85)
                    model = configure_genai(keys[attempts]); resp = model.generate_content(query); full_text = resp.text; success = True
                except Exception as e:
                    attempts += 1; last_e = str(e)
                    if attempts >= len(keys): st.error(f"❌ Lỗi: {last_e}"); st.stop()
                    time.sleep(1)
            up_p(ui["finalizing"], 100); time.sleep(0.3); prog_ph.empty()
            save_to_log(u_msg, full_text); save_to_csv(st.session_state.user_name, u_msg, full_text)
            parts = full_text.split("---TRÍCH DẪN NGUỒN---"); main_ans = parts[0].strip()
            ph = st.empty()
            if len(main_ans) > 500: ph.markdown(highlight_keywords(main_ans))
            else:
                typed = ""
                for c in main_ans: typed += c; ph.markdown(highlight_keywords(typed)); time.sleep(0.005)
            if len(parts) > 1:
                with st.expander("📖 Cơ sở văn bản"):
                    cits = parse_citations(full_text)
                    if cits:
                        cols = st.columns(len(cits) if len(cits) < 6 else 5)
                        for idx, (num, txt) in enumerate(cits.items()):
                            if cols[idx % 5].button(f"[{num}]", key=f"now_{num}"): st.session_state.view_cited_text = txt; st.rerun()
                    else: st.markdown(parts[1].strip())
            st.session_state.messages.append({"role": "assistant", "content": highlight_keywords(full_text)}); st.rerun()
