"""Local Streamlit interface for Arabic speech and voice cloning.

THESIS: A focused RTL voice workbench, not a dashboard.
OWN-WORLD: Thmanyah lettering, pale neutral canvas, ink controls, one quiet result surface.
STORY: Supply a key, choose a voice, write Arabic, listen and download; cloning is adjacent.
FIRST VIEWPORT: Title and connection at top, workflow tabs below, editor beside the result.
FORM: Direct shadcn V2 actions alongside native Streamlit audio and upload controls.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and docs/DESIGN.md.
"""

import base64
import os
import sys
from pathlib import Path

import streamlit as st
import streamlit_shadcn_ui as ui
from dotenv import load_dotenv
from streamlit.runtime import exists as streamlit_runtime_exists

if Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
    from arabic_tts import clone_voice, default_voice_id, speak
else:
    from app.arabic_tts import clone_voice, default_voice_id, speak


if __name__ == "__main__" and not streamlit_runtime_exists():
    os.execv(sys.executable, [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]])


load_dotenv()
st.set_page_config(page_title="استوديو الصوت العربي", page_icon="🎙️", layout="wide", initial_sidebar_state="collapsed")
font = base64.b64encode((Path(__file__).resolve().parent / "font" / "thmanyahsans-Bold.ttf").read_bytes()).decode()
st.markdown(
    f"""<style>
    @font-face {{ font-family: Thmanyah; src: url(data:font/ttf;base64,{font}) format('truetype'); font-weight: 700; }}
    .stApp {{ direction: rtl; text-align: right; background: #f7f8f7; color: #1c292d; }}
    .stApp, .stApp *:not([data-testid="stIconMaterial"]) {{ font-family: Thmanyah, sans-serif !important; }}
    [data-ssui-v2-host] {{ direction: rtl !important; }}
    [data-testid="stMainBlockContainer"] {{ max-width: 1120px; padding-top: 2.5rem; }}
    h1 {{ font-size: 2.2rem !important; line-height: 1.4 !important; }}
    h2 {{ font-size: 1.4rem !important; }}
    .stApp a {{ text-underline-offset: 3px; }}
    .stApp input[type=password], .stApp input[aria-label="معرّف الصوت"] {{ direction: ltr; text-align: left; }}
    @media (max-width: 640px) {{ [data-testid="stMainBlockContainer"] {{ padding: 1.25rem 1rem; }} }}
    </style>""",
    unsafe_allow_html=True,
)
header, connection = st.columns([3, 2], gap="large", vertical_alignment="top")
with header:
    st.title("استوديو الصوت العربي")
    st.caption("حوّل نصك إلى صوت عربي، بصوتك المستنسخ أو بصوت من المكتبة.")
with connection:
    with st.expander("مفتاح ElevenLabs API", expanded=not os.getenv("ELEVENLABS_API_KEY")):
        entered_api_key = st.text_input(
            "مفتاح API",
            type="password",
            help="يمكنك إدخال المفتاح هنا أو إضافته إلى ملف .env على جهازك.",
        )
api_key = entered_api_key or os.getenv("ELEVENLABS_API_KEY", "")

if not api_key:
    ui.alert("أدخل مفتاح API للبدء", "افتح إعداد المفتاح أعلاه وأدخل مفتاح ElevenLabs الخاص بك.")

active_tab = ui.tabs(["توليد الصوت", "استنساخ صوت"], key="workspace_tabs", label="سير العمل")

if active_tab == "توليد الصوت":
    saved_voice = default_voice_id()
    editor, result = st.columns([3, 2], gap="large", vertical_alignment="top")
    with editor:
        st.subheader("اكتب ما تريد سماعه")
        voice_source = ui.radio_group(
            "الصوت",
            ["صوتي المستنسخ", "صوت من المكتبة"],
            index=0 if saved_voice else 1,
            key="voice_source",
        )
        if voice_source == "صوتي المستنسخ":
            voice_id = saved_voice
            if not saved_voice:
                ui.alert("لا يوجد صوت محفوظ", "استنسخ صوتًا أولًا، أو اختر صوتًا من المكتبة.")
        else:
            st.caption("اختر صوتًا من [مكتبة ElevenLabs](https://elevenlabs.io/app/voice-library)، ثم الصق معرّفه.")
            voice_id = st.text_input("معرّف الصوت", placeholder="الصق معرّف الصوت من المكتبة")

        text = ui.textarea("النص العربي", placeholder="هلا والله، وش الأخبار؟", rows=7, key="speech_text")
        generate = ui.button("ولّد الصوت", key="generate", width="stretch")
        if generate:
            st.session_state.pop("audio", None)
            try:
                with st.spinner("جارٍ توليد الصوت…"):
                    st.session_state.audio = speak(text, voice_id, api_key)
            except ValueError as exc:
                st.warning(str(exc))
            except Exception:
                st.error("تعذّر توليد الصوت. تحقق من اتصالك بالإنترنت ومفتاح API ومعرّف الصوت، ثم أعد المحاولة.")

    with result:
        st.subheader("النتيجة")
        if st.session_state.get("audio"):
            st.audio(st.session_state.audio, format="audio/mp3")
            st.download_button("حمّل ملف MP3", st.session_state.audio, "speech.mp3", "audio/mpeg", use_container_width=True)
        else:
            ui.card("صوتك هنا", "اكتب نصًا واختر صوتًا، ثم اضغط «ولّد الصوت» للاستماع إلى النتيجة.")

else:
    st.subheader("استنسخ صوتك")
    st.caption("ارفع تسجيلًا لصوت تملك حق استنساخه. سيُستخدم حسابك في ElevenLabs لإنشاء الصوت.")
    clone_form, clone_help = st.columns([3, 2], gap="large", vertical_alignment="top")
    with clone_form:
        sample = st.file_uploader("التسجيل الصوتي", type=["wav", "mp3", "m4a"])
        name = ui.input("اسم الصوت", placeholder="صوتي العربي", key="clone_name")
        create = ui.button("استنسخ الصوت", key="clone", width="stretch")
        if create:
            try:
                with st.spinner("جارٍ استنساخ الصوت…"):
                    voice_id = clone_voice(sample.getvalue() if sample else b"", sample.name if sample else "", name, api_key)
                st.success(f"استنسخت صوتك وحفظته للاستخدام تلقائيًا. معرّف الصوت: {voice_id}")
            except ValueError as exc:
                st.warning(str(exc))
            except Exception:
                st.error("تعذّر استنساخ الصوت. تحقق من اتصالك بالإنترنت ومفتاح API والتسجيل، ثم أعد المحاولة.")
    with clone_help:
        ui.card("بعد الاستنساخ", "سيُحفظ الصوت على هذا الجهاز، ويمكنك اختياره من تبويب «توليد الصوت».")
