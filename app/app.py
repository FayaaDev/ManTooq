"""Local Streamlit interface for Arabic speech and voice cloning."""

import base64
import os
import secrets
import sys
from pathlib import Path

import streamlit as st
import streamlit_shadcn_ui as ui
from dotenv import load_dotenv
from streamlit.runtime import exists as streamlit_runtime_exists

if Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
    from arabic_tts import DEFAULT_SEED, clone_voice, default_voice_id, save_generated_audio, save_seed, saved_generated_audio, saved_seeds, speak
else:
    from app.arabic_tts import DEFAULT_SEED, clone_voice, default_voice_id, save_generated_audio, save_seed, saved_generated_audio, saved_seeds, speak


if __name__ == "__main__" and not streamlit_runtime_exists():
    os.execv(sys.executable, [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]])


load_dotenv()
st.set_page_config(page_title="استوديو الصوت العربي", page_icon="🎙️", layout="wide", initial_sidebar_state="collapsed")
font = base64.b64encode((Path(__file__).resolve().parent / "font" / "thmanyahsans-Bold.ttf").read_bytes()).decode()
st.markdown(
    f"""<style>
    @font-face {{ font-family: Thmanyah; src: url(data:font/ttf;base64,{font}) format('truetype'); font-weight: 700; }}
    .stApp {{ direction: rtl; text-align: right; background: #eaf0f3; color: #172c3a; }}
    .stApp, .stApp *:not([data-testid="stIconMaterial"]) {{ font-family: Thmanyah, sans-serif !important; }}
    [data-ssui-v2-host] {{ direction: rtl !important; }}
    [data-testid="stMainBlockContainer"] {{ max-width: 1200px; padding-top: 1.5rem; }}
    [data-testid="stMainBlockContainer"] > div > div {{ gap: 1rem; }}
    h1 {{ font-size: 1.65rem !important; line-height: 1.45 !important; letter-spacing: -.02em; }}
    h2, h3 {{ font-size: 1.2rem !important; }}
    .stApp a {{ text-underline-offset: 3px; color: #2254b4; }}
    .stApp ::selection {{ background: #bdd2f5; color: #142b3a; }}
    .stApp :focus-visible {{ outline-color: #2254b4; }}
    .stApp input[type=password], .stApp input[aria-label="معرّف الصوت"] {{ direction: ltr; text-align: left; }}
    .st-key-studio_sheet {{ background: #fff; border: 0; border-radius: 12px; padding: 2rem !important; box-shadow: 0 16px 45px rgba(28, 53, 70, .08); }}
    .st-key-studio_sheet [data-testid="stVerticalBlock"] {{ gap: .85rem; }}
    .st-key-studio_sheet textarea {{ font-size: 1.25rem; line-height: 1.9; background: #f7f9fa; border-color: #dce5ea; }}
    .st-key-studio_sheet textarea::placeholder {{ color: #536977; }}
    .st-key-playback {{ border-inline-start: 1px solid #dce5ea; padding-inline-start: 1.75rem; min-height: 390px; }}
    .st-key-playback [data-testid="stAudio"] {{ margin-top: 1.5rem; }}
    .st-key-clone_guidance {{ border-inline-start: 1px solid #dce5ea; padding-inline-start: 1.75rem; min-height: 240px; }}
    .st-key-studio_sheet [data-testid="stCode"] {{ direction: ltr; text-align: left; }}
    @media (max-width: 640px) {{
      [data-testid="stMainBlockContainer"] {{ padding: 1rem; }}
      .st-key-studio_sheet {{ padding: 1.25rem !important; }}
      .st-key-studio_sheet textarea {{ min-height: 210px; }}
      .st-key-playback {{ border-inline-start: 0; border-top: 1px solid #dce5ea; padding-inline-start: 0; padding-top: 1.25rem; min-height: 0; }}
      .st-key-clone_guidance {{ border-inline-start: 0; border-top: 1px solid #dce5ea; padding-inline-start: 0; padding-top: 1.25rem; min-height: 0; }}
    }}
    </style>""",
    unsafe_allow_html=True,
)
header, connection = st.columns([3, 1], gap="medium", vertical_alignment="center")
with header:
    st.title("استوديو الصوت العربي", text_alignment="right")
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

    with st.container(key="studio_sheet"):
        editor, result = st.columns([3, 2], gap="large", vertical_alignment="top")
        with editor:
            st.subheader("نصك، بصوتك", text_alignment="right")
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
                    ui.alert("لا يوجد صوت محفوظ", "استنسخ صوتًا أولًا، أو اختر صوتًا من المكتبة.")
            else:
                voice_id = st.text_input("معرّف الصوت", placeholder="معرّف الصوت من مكتبة ElevenLabs")

            with st.popover("إعدادات النبرة", icon=":material/tune:"):
                st.number_input("البذرة", min_value=0, max_value=2**32 - 1, step=1, key="speech_seed")
                if ui.button("بذرة جديدة", key="generate_seed", variant="ghost"):
                    st.session_state.speech_seed = secrets.randbits(32)
                    save_seed(st.session_state.speech_seed)
                st.selectbox("البذور المحفوظة", saved_seeds(), key="saved_seed", on_change=use_saved_seed)
            generate = ui.button("ولّد الصوت", key="generate", width="stretch")
            if generate:
                st.session_state.pop("audio", None)
                try:
                    with st.spinner("جارٍ توليد الصوت…"):
                        seed = int(st.session_state.speech_seed)
                        save_seed(seed)
                        st.session_state.audio = speak(text, voice_id, api_key, seed)
                        save_generated_audio(st.session_state.audio, seed)
                except ValueError as exc:
                    st.warning(str(exc))
                except Exception:
                    st.error("تعذّر توليد الصوت. تحقق من اتصالك بالإنترنت ومفتاح API ومعرّف الصوت، ثم أعد المحاولة.")

        with result:
            with st.container(key="playback"):
                st.subheader("الاستماع", text_alignment="right")
                if st.session_state.get("audio"):
                    st.audio(st.session_state.audio, format="audio/mp3")
                    st.download_button("حمّل ملف MP3", st.session_state.audio, "speech.mp3", "audio/mpeg", width="stretch")
                else:
                    st.caption("سيظهر التسجيل هنا بعد التوليد.", text_alignment="right")

elif active_tab == "استنساخ صوت":
    with st.container(key="studio_sheet"):
        clone_form, clone_help = st.columns([3, 2], gap="large", vertical_alignment="top")
        with clone_form:
            st.subheader("استنسخ صوتك", text_alignment="right")
            st.caption("ارفع تسجيلًا لصوت تملك حق استنساخه.", text_alignment="right")
            sample = st.file_uploader("التسجيل الصوتي", type=["wav", "mp3", "m4a"])
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
    st.subheader("الأصوات المحفوظة", text_alignment="right")
    recordings = saved_generated_audio()
    if not recordings:
        st.caption("ستظهر تسجيلاتك هنا بعد التوليد.", text_alignment="right")
    for index, (path, seed) in enumerate(recordings, 1):
        with st.container(border=True):
            title, details = st.columns([4, 1], vertical_alignment="center")
            with title:
                st.markdown(f"**تسجيل {index}**", text_alignment="right")
            with details:
                with ui.elements(key=f"seed_tip_{index}", width="content") as elements:
                    with elements.tooltip(f"رقم البذرة: {seed}"):
                        elements.button("البذرة", key=f"seed_{index}", variant="ghost", size="sm")
            st.audio(path, format="audio/mp3")
            st.download_button("حمّل ملف MP3", path.read_bytes(), path.name, "audio/mpeg", key=path.name)
