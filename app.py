import html
import json
import os
import time

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemini-3.8-flash"   # if you get "model not found", try "gemini-flash-latest"

st.set_page_config(page_title="Health Myth Checker", page_icon="🩺", layout="centered")

# ---------- Look and feel ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Hind', 'Segoe UI', sans-serif; }
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 2rem; max-width: 760px;}

.hero h1 {font-size: 2.3rem; font-weight: 700; color: #12343B; margin: 0 0 .2rem 0;}
.hero p  {font-size: 1.1rem; color: #3E5C62; margin: 0 0 1.2rem 0;}

.stTextArea textarea {
  font-size: 1.05rem; border-radius: 12px; border: 1.5px solid #9DB8B3; background: #fff;
}
.stTextArea textarea:focus {border-color: #0F766E; box-shadow: 0 0 0 2px #B6DDD7;}

div.stButton > button {
  border-radius: 999px; font-family: 'Hind', sans-serif; font-weight: 600; padding: .45rem 1.2rem;
}
div.stButton > button[kind="primary"] {background: #0F766E; border: none; color: #fff; padding: .55rem 2rem;}
div.stButton > button[kind="primary"]:hover {background: #0B5D56;}

.result {background: #fff; border: 1.5px solid #CFE0DC; border-radius: 16px; padding: 1.4rem 1.6rem; margin-top: 1.2rem;}
.stamp {
  display: inline-block; font-weight: 700; font-size: 1.5rem; padding: .15rem 1rem;
  border: 3px solid; border-radius: 8px; transform: rotate(-2deg); margin-bottom: .9rem;
}
.s-false      {color: #B3261E; background: #FDECEA;}
.s-misleading {color: #9A5200; background: #FFF1DC;}
.s-supported  {color: #1B7F3B; background: #E6F5EA;}
.s-unverified {color: #4A5E64; background: #ECF0F1;}
.claim {color: #5B7378; font-size: .95rem; margin-bottom: .5rem;}
.explain {font-size: 1.12rem; line-height: 1.6; color: #12343B; margin: .3rem 0 1rem 0;}
.srcs-title {font-weight: 600; color: #3E5C62; font-size: .95rem; margin-bottom: .35rem;}
.chip {display: inline-block; border: 1.5px solid #0F766E; color: #0F766E; border-radius: 999px;
       padding: .1rem .8rem; margin: 0 .4rem .4rem 0; font-size: .92rem; font-weight: 500;}
.note {color: #5B7378; font-size: .88rem; margin-top: .8rem;}
</style>
""", unsafe_allow_html=True)

# ---------- Setup ----------
def get_key():
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets["GEMINI_API_KEY"]   # used after deployment
    except Exception:
        return None

api_key = get_key()
if not api_key:
    st.error("API key missing. Add GEMINI_API_KEY to your .env file, then rerun.")
    st.stop()

client = genai.Client(api_key=api_key)

@st.cache_data
def load_facts():
    return pd.read_csv("facts.csv")

facts = load_facts()

knowledge = "\n\n".join(
    f"MYTH: {r.viral_myth}\nFACT: {r.scientific_fact}\nSOURCES: {r.verified_sources}"
    for r in facts.itertuples()
)

SYSTEM_PROMPT = f"""You are a health misinformation checker.
Use ONLY the knowledge base below. Never use outside knowledge or invent sources.
The user's message may be in English, Hindi or Hinglish. Write the explanation in the same language.

Return ONLY JSON with these keys:
"claim": the main health claim in the message, in one short sentence.
"verdict": exactly one of "False", "Misleading", "Supported", "Unverified".
"explanation": 2-4 simple sentences.
"sources": a list of source names from the matching entry, or [] if Unverified.

If the claim is not covered by the knowledge base, verdict MUST be "Unverified" and
the explanation should say it is not in the database and suggest asking a doctor.
Do not diagnose or give personal treatment advice.

KNOWLEDGE BASE:
{knowledge}
"""

STYLES = {"False": "s-false", "Misleading": "s-misleading",
          "Supported": "s-supported", "Unverified": "s-unverified"}


MODELS = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash"]

def check_claim(text):
    last_error = None
    for model in MODELS:                 # try each model in turn
        for attempt in range(2):         # two tries per model
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=text,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                data = json.loads(response.text)
                if data.get("verdict") not in STYLES:
                    data["verdict"] = "Unverified"
                return data
            except Exception as e:
                last_error = e
                time.sleep(1.5)          # short pause before retrying
    raise last_error
def set_text(value):
    st.session_state["text"] = value

# ---------- Page ----------
st.markdown("""
<div class="hero">
  <h1>🩺 Health Myth Checker</h1>
  <p>Got a health tip on WhatsApp? Paste it here and see what trusted sources say.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("**Try an example**")
examples = ["Lemon water cures cancer", "Hot water kills coronavirus", "Pineapple cures dengue"]
cols = st.columns(len(examples))
for col, ex in zip(cols, examples):
    col.button(ex, on_click=set_text, args=(ex,), use_container_width=True)

user_input = st.text_area(
    "Paste a message or type a claim",
    key="text", height=130,
    placeholder="Example: Subah garam paani me nimbu peene se cancer theek ho jata hai...",
)

if st.button("Check this claim", type="primary"):
    if not user_input.strip():
        st.warning("Type or paste a health claim first.")
    else:
        with st.spinner("Checking trusted sources..."):
            try:
                r = check_claim(user_input)
                sources = "".join(
                    f'<span class="chip">{html.escape(str(s))}</span>' for s in r.get("sources", [])
                )
                st.markdown(f"""
<div class="result">
  <div class="stamp {STYLES[r['verdict']]}">{html.escape(r['verdict'])}</div>
  <div class="claim">Claim checked: {html.escape(str(r.get('claim', '')))}</div>
  <div class="explain">{html.escape(str(r.get('explanation', '')))}</div>
  {'<div class="srcs-title">Sources</div>' + sources if sources else ''}
  <div class="note">This checks claims only. It is not medical advice. See a doctor for personal health decisions.</div>
</div>
""", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not complete the check. Details: {e}")

with st.sidebar:
    st.header("How it works")
    st.write("1. You paste a message.")
    st.write("2. The app reads the claim, even in Hindi or Hinglish.")
    st.write("3. It compares the claim with a hand-checked list of health myths.")
    st.write("4. If the claim isn't in the list, it says Unverified instead of guessing.")
    st.divider()
    st.metric("Claims in database", len(facts))
    st.caption("Covers a limited set of topics. Unverified does not mean true.")
