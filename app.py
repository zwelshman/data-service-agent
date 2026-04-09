import streamlit as st
import anthropic
from supabase import create_client

# ── BHF brand colours ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  :root {
    --bhf-red: #C8102E;
    --bhf-red-dark: #A00D24;
    --bhf-red-light: #F5E6E9;
  }
  .bhf-header {
    background-color: var(--bhf-red);
    padding: 1rem 1.5rem 0.75rem;
    border-radius: 8px;
    margin-bottom: 1.25rem;
  }
  .bhf-header h1 { color: white !important; margin: 0; font-size: 1.4rem; font-weight: 700; }
  .bhf-header p  { color: rgba(255,255,255,0.82); margin: 0; font-size: 0.78rem; }

  .bhf-card {
    background: var(--bhf-red-light);
    border-left: 4px solid var(--bhf-red);
    border-radius: 6px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
  }
  .source-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.6rem; }
  .source-pill {
    background: white;
    border: 1.5px solid var(--bhf-red);
    color: var(--bhf-red-dark);
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 600;
    text-decoration: none;
    display: inline-block;
  }
  .source-pill:hover { background: var(--bhf-red); color: white; }

  /* metric cards */
  .metric-row { display: flex; gap: 0.75rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
  .metric-card {
    background: white;
    border: 1px solid #e0c0c5;
    border-top: 3px solid var(--bhf-red);
    border-radius: 6px;
    padding: 0.6rem 1rem;
    flex: 1;
    min-width: 120px;
  }
  .metric-card .val { font-size: 1.35rem; font-weight: 700; color: var(--bhf-red-dark); }
  .metric-card .lbl { font-size: 0.72rem; color: #666; margin-top: 2px; }

  details summary { color: var(--bhf-red-dark) !important; font-weight: 600; }
  div[data-testid="stChatMessage"] a { color: var(--bhf-red-dark); }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="bhf-header">
  <h1>❤️ BHF DSC Assistant</h1>
  <p>BHF Data Science Centre · HDR UK · NHS England SDE</p>
</div>
""", unsafe_allow_html=True)

# ── Source pills ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="bhf-card">
  <strong>Sources available to this assistant:</strong>
  <div class="source-row">
    <a class="source-pill" href="https://github.com/BHFDSC/documentation" target="_blank">📄 BHFDSC/documentation</a>
    <a class="source-pill" href="https://github.com/BHFDSC/standard-pipeline" target="_blank">⚙️ BHFDSC/standard-pipeline</a>
    <a class="source-pill" href="https://bhfdatasciencecentre.org/dashboard/" target="_blank">📊 Dataset Summary Dashboard</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Supabase client ───────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

sb = get_supabase()

# ── Dataset explorer ──────────────────────────────────────────────────────────
with st.expander("📊 Dataset Explorer", expanded=False):

    # top-level metrics
    @st.cache_data(ttl=3600)
    def get_overall():
        res = sb.table("overall").select("*").execute()
        return res.data

    overall_data = get_overall()
    n_datasets = len({r["dataset"] for r in overall_data})
    latest_batch = max(r["archived_on"] for r in overall_data if r.get("archived_on"))
    total_records = sum(r["n"] for r in overall_data if r.get("n") and isinstance(r["n"], (int, float)))

    def fmt(n):
        if n >= 1_000_000_000: return f"{n/1e9:.1f}B"
        if n >= 1_000_000:     return f"{n/1e6:.1f}M"
        if n >= 1_000:         return f"{n/1e3:.1f}K"
        return str(n)

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card"><div class="val">{n_datasets}</div><div class="lbl">Datasets provisioned</div></div>
      <div class="metric-card"><div class="val">{fmt(total_records)}</div><div class="lbl">Total records (latest batch)</div></div>
      <div class="metric-card"><div class="val">{latest_batch}</div><div class="lbl">Latest batch archived on</div></div>
    </div>
    """, unsafe_allow_html=True)

    # dataset selector
    all_datasets = sorted({r["dataset"] for r in overall_data})
    selected = st.selectbox("Select a dataset", all_datasets, key="ds_select")

    if selected:
        ds_rows = [r for r in overall_data if r["dataset"] == selected]
        # most recent batch for this dataset
        latest = sorted(ds_rows, key=lambda r: r.get("archived_on", ""), reverse=True)[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total records", fmt(latest["n"]) if latest.get("n") else "—")
        col2.metric("Records with ID", fmt(latest["n_id"]) if latest.get("n_id") else "—")
        col3.metric("Distinct patients", str(latest.get("n_id_distinct", "—")))

        tab1, tab2 = st.tabs(["📈 Coverage over time", "✅ Column completeness"])

        with tab1:
            @st.cache_data(ttl=3600)
            def get_coverage(ds):
                res = sb.table("coverage").select("*").eq("dataset", ds).execute()
                return res.data

            cov = get_coverage(selected)
            if cov:
                import pandas as pd
                df_cov = pd.DataFrame(cov)
                df_cov = df_cov[df_cov["date_ym"].notna()].copy()
                df_cov["date_ym"] = pd.to_datetime(df_cov["date_ym"], errors="coerce")
                df_cov = df_cov.dropna(subset=["date_ym"]).sort_values("date_ym")
                if not df_cov.empty:
                    st.line_chart(df_cov.set_index("date_ym")[["n", "n_id"]])
            else:
                st.info("No coverage data for this dataset.")

        with tab2:
            @st.cache_data(ttl=3600)
            def get_completeness(ds):
                res = sb.table("completeness").select("*").eq("dataset", ds).execute()
                return res.data

            comp = get_completeness(selected)
            if comp:
                import pandas as pd
                df_comp = pd.DataFrame(comp)
                # latest batch only
                if "archived_on" in df_comp.columns:
                    latest_batch_comp = df_comp["archived_on"].max()
                    df_comp = df_comp[df_comp["archived_on"] == latest_batch_comp]
                df_comp = df_comp[["column_name", "completeness"]].dropna()
                df_comp["completeness"] = df_comp["completeness"].round(3)
                df_comp = df_comp.sort_values("completeness", ascending=False)
                st.dataframe(
                    df_comp.rename(columns={"column_name": "Column", "completeness": "Completeness"}),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No completeness data for this dataset.")

st.divider()

# ── Anthropic client & session ────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
AGENT_ID      = st.secrets["AGENT_ID"]
ENVIRONMENT_ID = st.secrets["ENVIRONMENT_ID"]
VAULT_ID      = st.secrets["VAULT_ID"]
BETAS         = ["managed-agents-2026-04-01"]

if "session_id" not in st.session_state:
    session = client.beta.sessions.create(
        agent=AGENT_ID,
        environment_id=ENVIRONMENT_ID,
        vault_ids=[VAULT_ID],
        title="Streamlit Session",
        betas=BETAS,
    )
    st.session_state.session_id = session.id
    st.session_state.messages = []

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        for step in msg.get("steps", []):
            if step["type"] == "thinking":
                with st.expander("💭 Thinking", expanded=False):
                    st.markdown(step["content"])
            elif step["type"] == "tool_use":
                with st.expander(f"🔧 Tool: `{step['name']}`", expanded=False):
                    if step.get("input"):
                        st.json(step["input"])
            elif step["type"] == "tool_result":
                with st.expander(f"📤 Result: `{step['name']}`", expanded=False):
                    st.markdown(step.get("content", ""))
        if msg["content"]:
            st.write(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about datasets, pipelines, phenotypes, codelists..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "steps": []})
    with st.chat_message("user"):
        st.write(prompt)

    client.beta.sessions.events.send(
        st.session_state.session_id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": prompt}]}],
        betas=BETAS,
    )

    with st.chat_message("assistant"):
        response_text = ""
        steps = []
        text_placeholder = st.empty()

        with client.beta.sessions.events.stream(
            session_id=st.session_state.session_id,
            betas=BETAS,
        ) as stream:
            for event in stream:

                if event.type == "agent.thinking":
                    thinking_text = getattr(event, "thinking", "")
                    if thinking_text:
                        with st.expander("💭 Thinking...", expanded=True):
                            st.markdown(thinking_text)
                        steps.append({"type": "thinking", "content": thinking_text})

                elif event.type == "agent.tool_use":
                    tool_name = getattr(event, "name", "unknown")
                    tool_input = getattr(event, "input", {})
                    with st.expander(f"🔧 Tool: `{tool_name}`", expanded=True):
                        if tool_input:
                            st.json(tool_input)
                    steps.append({"type": "tool_use", "name": tool_name, "input": tool_input})

                elif event.type == "agent.tool_result":
                    tool_name = getattr(event, "name", "unknown")
                    raw = getattr(event, "content", "") or getattr(event, "output", "")
                    result_content = raw if isinstance(raw, str) else " ".join(
                        getattr(b, "text", "") for b in raw
                    )
                    with st.expander(f"📤 Result: `{tool_name}`", expanded=False):
                        st.markdown(result_content or "_No output_")
                    steps.append({"type": "tool_result", "name": tool_name, "content": result_content})

                elif event.type == "agent.message":
                    for block in event.content:
                        if block.type == "text":
                            response_text += block.text
                            text_placeholder.write(response_text)

                elif event.type == "session.status_idle":
                    break

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "steps": steps,
    })
