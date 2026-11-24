"""Streamlit demonstration interface for Chopra & Haaland's original multi-agent logic.

This UI uses the project's original core.logic, core.agent, and core.manager.
It replaces the file-backed database with a per-browser-session in-memory adapter.
This is for fictional / non-sensitive demonstration interviews, not research data collection.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from pathlib import Path
import os
import sys
from uuid import uuid4

import streamlit as st

st.set_page_config(page_title="Chopra–Haaland | AI Interview Pilot", page_icon="🎓", layout="centered")

# The original repository imports `parameters` and `core` as top-level modules,
# because it runs `python app/app.py`. Preserve that import layout.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "app"))

# Read the API key from Streamlit's private Secrets or the OS environment.
# Never commit any .streamlit/secrets.toml file to a public repository.
api_key = os.environ.get("OPENAI_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", "") or st.secrets.get("KEY_OPENAI", "")
    except (FileNotFoundError, KeyError):
        api_key = ""
if not api_key:
    st.error("The OpenAI API key is not configured. Add KEY_OPENAI to the app's private Streamlit Secrets.")
    st.stop()
os.environ["OPENAI_API_KEY"] = api_key

# Import original multi-agent framework WITHOUT changing its agent prompts or workflow.
from parameters import INTERVIEW_PARAMETERS  # noqa: E402
from core import logic  # noqa: E402

PILOT_ID = "PILOT_INTERVIEW"
if PILOT_ID not in INTERVIEW_PARAMETERS:
    st.error("This package needs your local PILOT_INTERVIEW configuration in app/parameters.py.")
    st.stop()

# Context-local store avoids leaking interviews between visitors. The framework's
# session state is private to this Streamlit browser session; it is NOT persisted.
ACTIVE_STORE: ContextVar[dict | None] = ContextVar("active_interview_store", default=None)


class BrowserSessionDatabase:
    """Database interface expected by the original InterviewManager."""

    @staticmethod
    def _store() -> dict:
        store = ACTIVE_STORE.get()
        if store is None:
            raise RuntimeError("Interview database accessed outside a visitor session.")
        return store

    def load_remote_session(self, session_id: str):
        return deepcopy(self._store().get(session_id, []))

    def update_remote_session(self, session_id: str, history: list):
        assert history and history[-1]["session_id"] == session_id
        self._store()[session_id] = deepcopy(history)

    def delete_remote_session(self, session_id: str):
        self._store().pop(session_id, None)

    def retrieve_sessions(self, sessions=None):
        selected = sessions or self._store().keys()
        return [msg for sid in selected for msg in deepcopy(self._store().get(sid, []))]


# The original logic instantiates its file writer at import time, but all subsequent
# reads and writes go through this adapter; no interviews are saved as server files.
logic.db = BrowserSessionDatabase()


@contextmanager
def active_browser_store():
    token = ACTIVE_STORE.set(st.session_state.interview_histories)
    try:
        yield
    finally:
        ACTIVE_STORE.reset(token)


def clean_frontend_message(text: str) -> str:
    """Strip the original Flask/Qualtrics end-of-survey marker."""
    return text.replace("---END---", "").strip()


def new_session():
    for key in ("interview_histories", "interview_session_id", "interview_messages", "interview_finished"):
        st.session_state.pop(key, None)
    st.session_state.interview_histories = {}
    st.session_state.interview_session_id = uuid4().hex  # unguessable, not user-entered
    with active_browser_store():
        result = logic.begin_interview_session(st.session_state.interview_session_id, PILOT_ID)
    st.session_state.interview_messages = [{"role": "assistant", "content": clean_frontend_message(result["message"])}]
    st.session_state.interview_finished = False


def transcript_text() -> str:
    pieces = ["Chopra–Haaland Multi-Agent AI Interview — TEST TRANSCRIPT", "Demo only; not for research data collection", ""]
    for item in st.session_state.get("interview_messages", []):
        who = "Interviewer" if item["role"] == "assistant" else "Respondent"
        pieces.append(f"{who}: {item['content']}")
        pieces.append("")
    return "\n".join(pieces)


st.title("AI Qualitative Interview")
st.caption("Chopra–Haaland multi-agent framework · Streamlit demonstration")
st.warning("**Test only.** Please use fictional or non-sensitive answers. This is not an approved research data collection system.", icon="🔒")

with st.sidebar:
    st.header("About this pilot")
    st.write("The interview uses the original framework's probing, transition, summarization and moderation agents.")
    st.write("Topic: university experiences, challenges and support, and future aspirations.")
    st.write("Answers are kept only in this browser session; restarting or reloading may lose them. You can download your own test transcript.")
    st.caption("Chopra & Haaland, *Conducting Qualitative Interviews with AI* (2023). Non-commercial demonstration.")
    if st.session_state.get("interview_session_id"):
        if st.button("Start a fresh test", type="secondary", use_container_width=True):
            try:
                new_session()
                st.rerun()
            except Exception:
                st.error("Could not restart the interview. Check the app logs or API configuration.")

if "interview_session_id" not in st.session_state:
    st.write("This demonstration interviews a fictional student about their educational experiences and aspirations. You can explore how different AI agents generate follow-up questions and move between topics.")
    if st.button("Begin test interview", type="primary", use_container_width=True):
        try:
            new_session()
            st.rerun()
        except Exception:
            st.error("Could not start the interview. Please check the application configuration.")
    st.stop()

for entry in st.session_state.get("interview_messages", []):
    with st.chat_message(entry["role"]):
        st.write(entry["content"])

if st.session_state.get("interview_finished"):
    st.success("The interview has ended. You can save your test transcript below.")

user_input = st.chat_input("Write your response…", disabled=st.session_state.get("interview_finished", False))
if user_input and not st.session_state.interview_finished:
    if len(user_input) > 12000:
        st.error("Please shorten the response to 12,000 characters or fewer.")
    else:
        try:
            with st.spinner("Preparing the next interview question…"):
                with active_browser_store():
                    response = logic.next_question(
                        session_id=st.session_state.interview_session_id,
                        interview_id=PILOT_ID,
                        user_message=user_input,
                    )
        except Exception:
            st.error("The interview service could not process that answer. Please retry. No new answer was saved.")
        else:
            raw_message = response["message"]
            st.session_state.interview_messages.append({"role": "user", "content": user_input})
            st.session_state.interview_messages.append({"role": "assistant", "content": clean_frontend_message(raw_message)})
            if "---END---" in raw_message:
                st.session_state.interview_finished = True
            st.rerun()

st.divider()
st.download_button(
    "Download my test transcript (.txt)",
    transcript_text().encode("utf-8"),
    file_name="chopra_haaland_test_transcript.txt",
    mime="text/plain; charset=utf-8",
    use_container_width=True,
)
st.caption("No permanent transcript storage is configured. A public test link is not suitable for collecting identifiable research responses.")
