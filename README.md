# Health-Myth-Checker
Health Myth Checker lets you paste a health message or claim, in English, Hindi or Hinglish, and checks it against a hand-built database of 92 myths based on sources such as WHO, CDC and NHS. It returns a verdict (False, Misleading, Supported or Unverified) with a plain-language explanation and sources. If a claim is not in the database, it says “Unverified” instead of guessing. This is not medical advice.
## About this project

Built by **Devansh Maurya** for **[competition name]**, 2026.

**Problem:** Health myths spread quickly through WhatsApp forwards and many people can't tell which are false.

**What it does:** You paste a health message in English, Hindi or Hinglish. The app compares it with a hand-built database of 92 myths and facts, then shows a verdict, a plain-language explanation and the sources.

**Sources:** The database is based on guidance from organizations such as WHO, CDC, NHS and NCI. [Each entry was checked against its source page.]

**What I did:** I chose the problem, collected and checked the database, tested the app, and decided that it should say "Unverified" instead of guessing.

**AI assistance:** I used an AI assistant to help write and explain the code, and an AI model (Google Gemini) inside the app to read the message and match it to the database.

**Limitations:** The app only covers the 92 topics in its database. "Unverified" does not mean a claim is true. It is not medical advice, so please see a doctor for personal health decisions.

**Live app:** health-myth-checker.streamlit.app
