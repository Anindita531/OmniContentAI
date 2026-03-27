import streamlit as st
import os
from main import app as langgraph_app
from dotenv import load_dotenv

# PDF (Unicode & Bengali Support)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ------------------ INIT ------------------
load_dotenv()
st.set_page_config(page_title="OmniContent AI", layout="wide")

# ------------------ SESSION ------------------
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "final" not in st.session_state:
    st.session_state.final = None

# ------------------ PDF GENERATION ------------------
def generate_pdf(res):
    file_path = "OmniContent_Report.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    # 1. Register the Bengali Font (Ensure this file is in your folder!)
    try:
        pdfmetrics.registerFont(TTFont('BengaliFont', 'NotoSansBengali-Regular.ttf'))
        # Create a custom style for Bengali
        bengali_style = ParagraphStyle(
            'BengaliStyle',
            parent=styles['Normal'],
            fontName='BengaliFont',
            fontSize=11,
            leading=14
        )
    except Exception as e:
        st.error(f"Font Error: {e}. Make sure 'NotoSansBengali-Regular.ttf' is in the directory.")
        return None

    story = []
    story.append(Paragraph("OmniContent AI Report", styles["Title"]))
    story.append(Spacer(1, 12))

    # Channels (English-centric)
    for key in ["linkedin", "twitter", "newsletter"]:
        if res.get(key):
            story.append(Paragraph(f"<b>{key.upper()}</b>", styles["Heading2"]))
            story.append(Paragraph(res[key], styles["Normal"]))
            story.append(Spacer(1, 10))

    # Languages (Localized)
    for lang, text in res.get("localizations", {}).items():
        story.append(Paragraph(f"<b>{lang}</b>", styles["Heading2"]))
        
        # If the language is Bengali, use the registered font style
        current_style = bengali_style if lang.lower() == "bengali" else styles["Normal"]
        story.append(Paragraph(text, current_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    return file_path

# ------------------ CSS ------------------
st.markdown("""
<style>
body {background:#050505;color:white;}
.glass {
    padding:15px;
    border-radius:15px;
    background: rgba(255,255,255,0.05);
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ CARD COMPONENT ------------------
def card(title, text, key):
    st.markdown(f"""<div class="glass"><b>{title}</b><hr></div>""", unsafe_allow_html=True)
    st.write(text)  # Streamlit handles Unicode/Bengali natively
    
    st.text_area(
        "Copy here",
        value=text,
        key=f"text_{key}",
        height=120
    )
    if st.button(f"📋 Copy {title}", key=f"btn_{key}"):
        st.toast(f"{title} ready to copy!")

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.subheader("⚙️ Config")
    campaign_id = st.text_input("Campaign ID", "AI_2026")
    languages = st.multiselect(
        "Languages",
        ["English","Bengali","Hindi","Spanish","French","German"],
        default=["English", "Bengali"]
    )
    tone = st.selectbox("Tone", ["Professional","Casual"])
    platforms = st.multiselect(
        "Platforms",
        ["LinkedIn","Twitter","Email"],
        default=["LinkedIn"]
    )

# ------------------ MAIN ------------------
col1, col2 = st.columns([1,1.2])

with col1:
    st.subheader("🧠 Input")
    task = st.text_area("Campaign Brief")

    if st.button("🚀 Generate"):
        config = {"configurable": {"thread_id": campaign_id}}
        for event in langgraph_app.stream({
            "task": task,
            "target_languages": languages,
            "tone": tone,
            "platforms": platforms
        }, config, stream_mode="values"):
            if event.get("content"):
                st.session_state.draft = event["content"]

    if st.session_state.draft:
        card("Draft", st.session_state.draft, "draft")
        if st.button("🌍 Finalize"):
            config = {"configurable": {"thread_id": campaign_id}}
            for event in langgraph_app.stream(None, config, stream_mode="values"):
                if event.get("final_assets"):
                    st.session_state.final = event["final_assets"]

with col2:
    st.subheader("📊 Output")
    if st.session_state.final:
        res = st.session_state.final

        if res.get("linkedin"): card("LinkedIn", res["linkedin"], "linkedin")
        if res.get("twitter"): card("Twitter", res["twitter"], "twitter")
        if res.get("newsletter"): card("Newsletter", res["newsletter"], "newsletter")

        for lang, text in res.get("localizations", {}).items():
            card(lang, text, f"lang_{lang}")

        st.markdown("### 📄 Export")
        if st.button("Generate PDF"):
            file = generate_pdf(res)
            if file:
                with open(file, "rb") as f:
                    st.download_button(
                        "⬇ Download PDF",
                        f,
                        file_name="OmniContent_Report.pdf",
                        mime="application/pdf"
                    )
    else:
        st.info("Run pipeline to see results 🚀")