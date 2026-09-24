# استوديو الصوت العربي — interface

Operate-mode, RTL voice workbench. The generating task leads; cloning stays one tab away. The first desktop viewport places text and voice controls on the right and playback on the left; narrow screens stack controls before results.

- **Type:** bundled Thmanyah font throughout the Arabic interface. API keys and voice IDs read left-to-right.
- **Color:** light neutral canvas (`#f7f8f7`), ink (`#1c292d`), white input and result surfaces. Primary shadcn actions use their native dark style.
- **Components:** streamlit-shadcn-ui V2 tabs, radio group, textarea, name input, buttons, alert and informational card; native Streamlit key field, file upload, audio and download. Components inherit RTL from their V2 host; Streamlit's light theme keeps both systems legible.
- **Feedback:** empty result teaches the next action; validation appears beside the initiating control; generated audio becomes playable and downloadable. Cloning confirms the saved ID.
