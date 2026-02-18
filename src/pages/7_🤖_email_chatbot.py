"""Side-by-side chatbot page that compares OpenAI and Bedrock responses."""

import streamlit as st

from llm.guardrails import action_guardrail_message, is_action_request
from llm.service import generate_fallback_response, run_provider, test_provider_connection
from utils.db import DatabaseManager

db = DatabaseManager()


def _init_state() -> None:
    """Initialize chat histories and per-provider metrics in Streamlit state."""
    if "chat_history_openai" not in st.session_state:
        st.session_state.chat_history_openai = [
            {
                "role": "assistant",
                "content": "OpenAI assistant is ready for drafting and app-grounded help.",
            }
        ]
    if "chat_history_bedrock" not in st.session_state:
        st.session_state.chat_history_bedrock = [
            {
                "role": "assistant",
                "content": "Bedrock Nova Micro assistant is ready for drafting and app-grounded help.",
            }
        ]
    if "metrics_openai" not in st.session_state:
        st.session_state.metrics_openai = []
    if "metrics_bedrock" not in st.session_state:
        st.session_state.metrics_bedrock = []


def _render_provider_panel(title: str, history_key: str, metrics_key: str) -> None:
    """Render one provider panel with latest metrics and full conversation."""
    st.subheader(title)
    metrics = st.session_state[metrics_key]
    if metrics:
        last = metrics[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("Latency (ms)", "n/a" if last.get("latency_ms") is None else f"{last.get('latency_ms')}")
        col2.metric("Total Tokens", "n/a" if last.get("total_tokens") is None else f"{last.get('total_tokens')}")
        col3.metric(
            "Response Chars",
            "n/a" if last.get("response_chars") is None else f"{last.get('response_chars')}",
        )
        if last.get("error"):
            st.caption(f"Last provider error: {last.get('error')}")
    else:
        st.caption("No metrics yet.")

    st.caption("Conversation")
    for message in st.session_state[history_key]:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def _render_comparison() -> None:
    """Show deltas between the latest OpenAI and Bedrock metric snapshots."""
    openai_metrics = st.session_state.metrics_openai
    bedrock_metrics = st.session_state.metrics_bedrock
    if not openai_metrics or not bedrock_metrics:
        st.caption("Metric comparison will appear after the first shared prompt.")
        return

    o_last = openai_metrics[-1]
    b_last = bedrock_metrics[-1]

    def _to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    o_latency = _to_float(o_last.get("latency_ms"))
    b_latency = _to_float(b_last.get("latency_ms"))
    o_chars = _to_float(o_last.get("response_chars"))
    b_chars = _to_float(b_last.get("response_chars"))
    o_tokens = _to_float(o_last.get("total_tokens"))
    b_tokens = _to_float(b_last.get("total_tokens"))

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Latency Delta (OpenAI-Bedrock)",
        "n/a" if o_latency is None or b_latency is None else f"{round(o_latency - b_latency, 2)} ms",
    )
    c2.metric(
        "Token Delta (OpenAI-Bedrock)",
        "n/a" if o_tokens is None or b_tokens is None else f"{int(o_tokens - b_tokens)}",
    )
    c3.metric(
        "Chars Delta (OpenAI-Bedrock)",
        "n/a" if o_chars is None or b_chars is None else f"{int(o_chars - b_chars)}",
    )


def main():
    """Render the chatbot comparison UI and run both providers on shared prompts."""
    st.title("Email Chatbot Comparison")
    st.caption("Same prompt to OpenAI and Bedrock Nova Micro with shared RAG/guardrails and side-by-side metrics.")
    st.divider()
    _init_state()

    test_cols = st.columns(2)
    if test_cols[0].button("Test OpenAI", use_container_width=True):
        with st.spinner("Testing OpenAI..."):
            ok, message = test_provider_connection("openai")
        if ok:
            st.success(message)
        else:
            st.error(message)

    if test_cols[1].button("Test Bedrock", use_container_width=True):
        with st.spinner("Testing Bedrock..."):
            ok, message = test_provider_connection("bedrock")
        if ok:
            st.success(message)
        else:
            st.error(message)

    left, right = st.columns(2)
    with left:
        _render_provider_panel("OpenAI", "chat_history_openai", "metrics_openai")
    with right:
        _render_provider_panel("Bedrock Nova Micro", "chat_history_bedrock", "metrics_bedrock")
    st.divider()
    st.subheader("Latest Metrics Delta")
    _render_comparison()

    if prompt := st.chat_input("Send same prompt to both models..."):
        st.session_state.chat_history_openai.append({"role": "user", "content": prompt})
        st.session_state.chat_history_bedrock.append({"role": "user", "content": prompt})

        if is_action_request(prompt):
            response_openai = action_guardrail_message()
            response_bedrock = action_guardrail_message()
            openai_metrics = {"latency_ms": 0, "total_tokens": "n/a", "response_chars": len(response_openai)}
            bedrock_metrics = {"latency_ms": 0, "total_tokens": "n/a", "response_chars": len(response_bedrock)}
        else:
            openai_result = run_provider("openai", prompt, st.session_state.chat_history_openai, db)
            bedrock_result = run_provider("bedrock", prompt, st.session_state.chat_history_bedrock, db)

            response_openai = openai_result.text or generate_fallback_response(prompt, db)
            response_bedrock = bedrock_result.text or generate_fallback_response(prompt, db)
            openai_metrics = dict(openai_result.metrics)
            bedrock_metrics = dict(bedrock_result.metrics)
            if openai_result.error:
                openai_metrics["error"] = openai_result.error
            if bedrock_result.error:
                bedrock_metrics["error"] = bedrock_result.error

        st.session_state.chat_history_openai.append({"role": "assistant", "content": response_openai})
        st.session_state.chat_history_bedrock.append({"role": "assistant", "content": response_bedrock})
        st.session_state.metrics_openai.append(openai_metrics)
        st.session_state.metrics_bedrock.append(bedrock_metrics)
        st.rerun()


if __name__ == "__main__":
    main()
