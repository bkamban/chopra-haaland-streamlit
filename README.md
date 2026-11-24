# Chopra–Haaland Multi-Agent Interview — Streamlit Demo

This is a **non-commercial test adaptation** of Felix Chopra and Ingar Haaland,
*Conducting Qualitative Interviews with AI* (2023),
https://github.com/fchop/interviews (CC BY-NC 4.0).

Uses original `core/logic.py`, `core/agent.py`, `core/manager.py`,
`core/auxiliary.py`, and the local `PILOT_INTERVIEW` parameter configuration.
Only the frontend and storage adapter are new. Multi-agent workflow remains intact.

## Deploy with Streamlit Community Cloud

- Python version: **3.12** (set under Advanced settings).
- Branch: `main`.
- Main file: `streamlit_app.py`.
- Private Secrets (in Streamlit dashboard, not GitHub):
  `KEY_OPENAI = "YOUR_NEW_OPENAI_API_KEY"`.

## Privacy

Demo only; instruct reviewers to use fictional, non-sensitive responses.
Chat state is per visitor and in memory, not saved durably.
Respondents can download their own transcript; reloading may lose the session.
This is not an approved production interview/retention or GDPR setup.
