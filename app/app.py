"""Local Streamlit interface for Arabic speech and voice cloning."""

import base64
import os
import secrets
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit_shadcn_ui as ui
from dotenv import load_dotenv
from streamlit.runtime import exists as streamlit_runtime_exists

if getattr(sys, "frozen", False) or Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
    from arabic_tts import DEFAULT_SEED, clone_voice, default_voice_id, save_generated_audio, save_seed, saved_generated_audio, saved_seeds, speak
else:
    from app.arabic_tts import DEFAULT_SEED, clone_voice, default_voice_id, save_generated_audio, save_seed, saved_generated_audio, saved_seeds, speak


if __name__ == "__main__" and not streamlit_runtime_exists():
    os.execv(sys.executable, [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]])


load_dotenv()
st.set_page_config(page_title="منطوق", page_icon="🎙️", layout="wide", initial_sidebar_state="collapsed")
font = base64.b64encode((Path(__file__).resolve().parent / "font" / "thmanyahsans-Bold.ttf").read_bytes()).decode()
st.markdown(
    f"""<style>
    @font-face {{ font-family: Thmanyah; src: url(data:font/ttf;base64,{font}) format('truetype'); font-weight: 700; }}
    .stApp {{ direction: rtl; text-align: right; background: #fff; color: #171717; }}
    .stApp, .stApp *:not([data-testid="stIconMaterial"]) {{ font-family: Thmanyah, sans-serif !important; }}
    [data-ssui-v2-host] {{ direction: rtl !important; }}
    [data-testid="stMainBlockContainer"] {{ max-width: 1100px; padding-top: 1.5rem; padding-bottom: 2rem; }}
    [data-testid="stMainBlockContainer"] > div > div {{ gap: 1rem; }}
    h1 {{ font-size: 1.65rem !important; line-height: 1.45 !important; letter-spacing: -.02em; }}
    h2, h3 {{ font-size: 1.2rem !important; }}
    .stApp a {{ text-underline-offset: 3px; color: #111; }}
    .stApp ::selection {{ background: #deded9; color: #171717; }}
    .stApp :focus-visible {{ outline-color: #111; }}
    .stApp input[type=password], .stApp input[aria-label="معرّف الصوت"] {{ direction: ltr; text-align: left; }}
    .st-key-studio_sheet {{ background: #fff; border: 1px solid #e2e2de; border-radius: 10px; padding: 2rem !important; }}
    .st-key-studio_sheet [data-testid="stVerticalBlock"] {{ gap: .85rem; }}
    .st-key-studio_sheet textarea {{ font-size: 1.25rem; line-height: 1.9; background: #f6f6f4; border-color: #e2e2de; }}
    .st-key-studio_sheet textarea::placeholder {{ color: #666; }}
    .st-key-playback {{ border-inline-start: 1px solid #e2e2de; padding-inline-start: 1.75rem; min-height: 390px; }}
    .st-key-playback [data-testid="stAudio"] {{ margin-top: 1.5rem; }}
    .st-key-clone_guidance {{ border-inline-start: 1px solid #e2e2de; padding-inline-start: 1.75rem; min-height: 240px; }}
    .st-key-studio_sheet [data-testid="stCode"] {{ direction: ltr; text-align: left; }}
    .st-key-app_header {{ position: sticky; top: 0; z-index: 10; background: #fff; border-bottom: 1px solid #e2e2de; margin-bottom: 1.5rem; padding-block: .9rem; }}
    .st-key-app_header [data-testid="stVerticalBlock"] {{ gap: 0; }}
    .st-key-app_header h1 {{ margin: 0; }}
    .st-key-app_header [data-testid="stCaptionContainer"] {{ color: #666; }}
    .st-key-footer {{ border-top: 1px solid #e2e2de; margin-top: 3rem; padding-top: 2rem; }}
    .st-key-footer .manfath-logo {{ display: block; width: 144px; max-width: 100%; margin-inline: auto; }}
    @media (max-width: 640px) {{
      [data-testid="stMainBlockContainer"] {{ padding: 1rem; }}
      .st-key-studio_sheet {{ padding: 1.25rem !important; }}
      .st-key-studio_sheet textarea {{ min-height: 210px; }}
      .st-key-playback {{ border-inline-start: 0; border-top: 1px solid #e2e2de; padding-inline-start: 0; padding-top: 1.25rem; min-height: 0; }}
      .st-key-clone_guidance {{ border-inline-start: 0; border-top: 1px solid #e2e2de; padding-inline-start: 0; padding-top: 1.25rem; min-height: 0; }}
    }}
    </style>""",
    unsafe_allow_html=True,
)
with st.container(key="app_header"):
    header, connection = st.columns([3, 1], gap="medium", vertical_alignment="center")
    with header:
        st.title("منطوق", text_alignment="right")
        st.caption("مساحة العمل الصوتي العربية", text_alignment="right")
    with connection:
        with st.popover("مفتاح API", icon=":material/key:"):
            entered_api_key = st.text_input(
                "مفتاح API",
                type="password",
                help="أدخل مفتاح ElevenLabs أو أضفه إلى .env على جهازك.",
            )
api_key = entered_api_key or os.getenv("ELEVENLABS_API_KEY", "")

if not api_key:
    ui.alert("مفتاح API مطلوب", "أضف مفتاح ElevenLabs من الزر أعلاه قبل التوليد.")

active_tab = ui.tabs(["توليد الصوت", "استنساخ صوت", "الأصوات المحفوظة"], key="workspace_tabs", label="سير العمل")

if active_tab == "توليد الصوت":
    saved_voice = default_voice_id()
    st.session_state.setdefault("speech_seed", DEFAULT_SEED)

    def use_saved_seed():
        st.session_state.speech_seed = int(st.session_state.saved_seed)

    def generate_seed():
        st.session_state.speech_seed = secrets.randbits(32)
        save_seed(st.session_state.speech_seed)

    with st.container(key="studio_sheet"):
        editor, result = st.columns([3, 2], gap="large", vertical_alignment="top")
        with editor:
            st.header("نصك، بصوتك", text_alignment="right")
            text = st.text_area("النص العربي", placeholder="اكتب النص الذي تريد سماعه…", height=240, key="speech_text")
            voice_source = ui.radio_group(
                "الصوت",
                ["صوتي المستنسخ", "صوت من المكتبة"],
                index=0 if saved_voice else 1,
                key="voice_source",
            )
            if voice_source == "صوتي المستنسخ":
                voice_id = saved_voice
                if not saved_voice:
                    ui.alert("لا يوجد صوت محفوظ", "افتح تبويب «استنساخ صوت» لإنشاء صوتك، أو اختر صوتًا من المكتبة.")
            else:
                voice_id = st.text_input("معرّف الصوت", placeholder="معرّف الصوت من مكتبة ElevenLabs", help="انسخ معرّف الصوت من مكتبة ElevenLabs والصقه هنا.")

            with st.popover("إعدادات النبرة", icon=":material/tune:"):
                st.number_input("البذرة", min_value=0, max_value=2**32 - 1, step=1, key="speech_seed", help="استخدم الرقم نفسه لتكرار إعداد النبرة.")
                ui.button("بذرة جديدة", key="generate_seed", variant="ghost", on_click=generate_seed)
                st.selectbox("البذور المحفوظة", saved_seeds(), key="saved_seed", on_change=use_saved_seed)
            if not api_key:
                st.caption("أضف مفتاح API من أعلى الصفحة قبل التوليد.", text_alignment="right")
            elif not voice_id:
                st.caption("اختر صوتًا محفوظًا أو أدخل معرّف صوت من المكتبة.", text_alignment="right")
            elif not text.strip():
                st.caption("اكتب النص العربي لبدء التوليد.", text_alignment="right")
            else:
                st.caption("يُرسل النص إلى ElevenLabs عند التوليد، وقد تُحتسب تكلفة الاستخدام.", text_alignment="right")
            generate = ui.button("ولّد الصوت", key="generate", width="stretch")
            if generate:
                try:
                    with st.spinner("جارٍ توليد الصوت…"):
                        seed = int(st.session_state.speech_seed)
                        save_seed(seed)
                        audio = speak(text, voice_id, api_key, seed)
                        save_generated_audio(audio, seed)
                        st.session_state.audio = audio
                except ValueError as exc:
                    st.warning(str(exc))
                except Exception:
                    st.error("تعذّر توليد الصوت. تحقق من اتصالك بالإنترنت ومفتاح API ومعرّف الصوت، ثم أعد المحاولة.")

        with result:
            with st.container(key="playback"):
                st.header("الاستماع", text_alignment="right")
                if st.session_state.get("audio"):
                    st.audio(st.session_state.audio, format="audio/mp3")
                    st.download_button("حمّل ملف MP3", st.session_state.audio, "speech.mp3", "audio/mpeg", width="stretch")
                else:
                    st.caption("سيظهر التسجيل هنا بعد التوليد.", text_alignment="right")

elif active_tab == "استنساخ صوت":
    with st.container(key="studio_sheet"):
        clone_form, clone_help = st.columns([3, 2], gap="large", vertical_alignment="top")
        with clone_form:
            st.header("استنسخ صوتك", text_alignment="right")
            st.caption("ارفع تسجيلًا لصوت تملك حق استنساخه.", text_alignment="right")
            sample = st.file_uploader("التسجيل الصوتي", type=["wav", "mp3", "m4a"])
            st.caption("ملفات WAV أو MP3 أو M4A، بحجم لا يتجاوز 200 ميجابايت.", text_alignment="right")
            name = ui.input("اسم الصوت", placeholder="صوتي العربي", key="clone_name")
            create = ui.button("استنسخ الصوت", key="clone", width="stretch")
            if create:
                try:
                    with st.spinner("جارٍ استنساخ الصوت…"):
                        voice_id = clone_voice(sample.getvalue() if sample else b"", sample.name if sample else "", name, api_key)
                    st.success("استنسخت صوتك وحفظته للاستخدام تلقائيًا.")
                    st.code(voice_id)
                except ValueError as exc:
                    st.warning(str(exc))
                except Exception:
                    st.error("تعذّر استنساخ الصوت. تحقق من اتصالك بالإنترنت ومفتاح API والتسجيل، ثم أعد المحاولة.")
        with clone_help:
            with st.container(key="clone_guidance"):
                st.caption("يُحفظ الصوت على هذا الجهاز ويظهر في تبويب «توليد الصوت».", text_alignment="right")

else:
    st.header("الأصوات المحفوظة", text_alignment="right")
    recordings = saved_generated_audio()
    if not recordings:
        st.caption("ستظهر تسجيلاتك هنا بعد التوليد.", text_alignment="right")
    for index, (path, seed) in enumerate(recordings, 1):
        with st.container(border=True):
            title, details = st.columns([4, 1], vertical_alignment="center")
            with title:
                st.markdown(f"**تسجيل {index}**", text_alignment="right")
                st.caption(datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y/%m/%d · %H:%M"), text_alignment="right")
            with details:
                with ui.elements(key=f"seed_tip_{index}", width="content") as elements:
                    with elements.tooltip(f"رقم البذرة: {seed}"):
                        elements.button("البذرة", key=f"seed_{index}", variant="ghost", size="sm")
            st.audio(path, format="audio/mp3")
            st.download_button("حمّل ملف MP3", path.read_bytes(), path.name, "audio/mpeg", key=path.name)

with st.container(key="footer"):
    brand, attribution, copyright = st.columns(3, gap="large", vertical_alignment="center")
    with brand:
        st.markdown("**منطوق**", text_alignment="right")
    with attribution:
        logo = base64.b64encode((Path(__file__).resolve().parent / "font" / "manfath-logo.png").read_bytes()).decode()
        st.markdown(f'<img class="manfath-logo" src="data:image/png;base64,{logo}" alt="منفذ">', unsafe_allow_html=True)
        st.caption("أحد منتجات منفذ", text_alignment="center")
    with copyright:
        st.caption(f"© {datetime.now().year} منطوق. جميع الحقوق محفوظة.", text_alignment="right")
