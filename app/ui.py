"""Streamlit chat UI for the coffee-chain text-to-SQL assistant."""
import streamlit as st

from ask import generate_sql, load_schema, run_sql

st.set_page_config(page_title="Coffee Chain Text-to-SQL", page_icon="☕", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1100px;}
    .hero {
        background: linear-gradient(135deg, #6F4E37 0%, #A47551 100%);
        color: #FFFFFF; padding: 1.6rem 2rem; border-radius: 18px; margin-bottom: 1.2rem;
    }
    .hero h1 {color: #FFFFFF; margin: 0; font-size: 2rem;}
    .hero p {margin: 0.4rem 0 0; opacity: 0.9;}
    div[data-testid="stChatMessage"] {border-radius: 14px;}
    [data-testid="stChatMessageAvatarUser"] {background-color: #6F4E37 !important; color: #FFFFFF !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

EXAMPLES = [
    "สาขาไหนขายได้มากที่สุด 5 อันดับแรก",
    "เมนูเครื่องดื่มที่ขายดีที่สุด 10 อันดับ",
    "ยอดขายแต่ละเดือนในปี 2026",
    "Which payment method is used most often?",
    "How many Gold members do we have?",
]


@st.cache_resource
def cached_schema():
    return load_schema(include_checks=True)


@st.cache_data(show_spinner=False)
def cached_sql(question):
    return generate_sql(question, cached_schema())


@st.cache_data(show_spinner=False)
def cached_result(sql):
    return run_sql(sql)


def chart_columns(df):
    """Return (label_col, value_col) if the result looks chartable, else None."""
    if len(df) < 2 or len(df.columns) < 2:
        return None
    numeric = df.select_dtypes("number").columns
    first = df.columns[0]
    if first in numeric or len(numeric) == 0:
        return None
    return first, numeric[0]


def answer(question):
    msg = {"role": "assistant"}
    try:
        msg["sql"] = cached_sql(question)
    except Exception as e:
        msg["error"] = f"Could not reach the LLM: {e}"
        return msg
    try:
        msg["df"] = cached_result(msg["sql"])
    except Exception as e:
        msg["error"] = f"The generated SQL failed to run: {e}"
    return msg


def render_answer(msg):
    if msg.get("error"):
        st.error(msg["error"])
    if "sql" not in msg:
        return
    df = msg.get("df")
    if df is None:
        st.code(msg["sql"], language="sql")
        return
    st.markdown(f"Found **{len(df):,}** row(s).")
    tab_result, tab_sql, tab_chart = st.tabs([":material/table_chart: Result", ":material/code: SQL", ":material/bar_chart: Chart"])
    with tab_result:
        st.dataframe(df, hide_index=True)
    with tab_sql:
        st.code(msg["sql"], language="sql")
    with tab_chart:
        cols = chart_columns(df)
        if cols:
            st.bar_chart(df.set_index(cols[0])[cols[1]])
        else:
            st.caption("No chart for this result.")


if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ☕ About")
    st.write(
        "Ask questions about a coffee-chain database (50 branches, 200k+ orders) "
        "in Thai or English. An LLM writes the SQL, which runs on a read-only MySQL account."
    )
    st.markdown("### :material/lightbulb: Try asking")
    for example in EXAMPLES:
        if st.button(example, width="stretch"):
            st.session_state.pending = example
    st.divider()
    if st.button("Clear chat", icon=":material/delete:", width="stretch"):
        st.session_state.messages = []
        st.rerun()
    with st.expander("Database schema", icon=":material/schema:"):
        st.code(cached_schema(), language="text")
    st.caption("Python · MySQL 8 · Gemini · Streamlit")

# ---------- Main ----------
st.markdown(
    """
    <div class="hero">
      <h1>☕ Coffee Chain Text-to-SQL</h1>
      <p>Ask questions about the coffee-chain database in Thai or English.
      The app turns your question into SQL and fetches the answer from MySQL.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.info("Pick an example from the sidebar, or type your own question below.")

for msg in st.session_state.messages:
    avatar = "☕" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            render_answer(msg)

question = st.chat_input("Ask about sales, menu items, branches, members...")
question = question or st.session_state.pop("pending", None)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant", avatar="☕"):
        with st.spinner("Writing SQL and fetching data..."):
            msg = answer(question)
        render_answer(msg)
    st.session_state.messages.append(msg)
