import streamlit as st
import anthropic
import json

# ── BHF brand colours ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  :root { --bhf-red: #C8102E; --bhf-red-dark: #A00D24; --bhf-red-light: #F5E6E9; }

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
    background: white; border: 1.5px solid var(--bhf-red);
    color: var(--bhf-red-dark); border-radius: 20px;
    padding: 0.25rem 0.75rem; font-size: 0.78rem; font-weight: 600;
    text-decoration: none; display: inline-block;
  }
  .source-pill:hover { background: var(--bhf-red); color: white; }

  .metric-row { display: flex; gap: 0.75rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
  .metric-card {
    background: white; border: 1px solid #e0c0c5;
    border-top: 3px solid var(--bhf-red); border-radius: 6px;
    padding: 0.6rem 1rem; flex: 1; min-width: 120px;
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

# ── Anthropic client ──────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
AGENT_ID       = st.secrets["AGENT_ID"]
ENVIRONMENT_ID = st.secrets["ENVIRONMENT_ID"]
VAULT_ID       = st.secrets["VAULT_ID"]
BETAS          = ["managed-agents-2026-04-01"]

# ── Session init ──────────────────────────────────────────────────────────────
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

# ── Helper: send a prompt to the agent and return the text response ────────────
def query_agent(prompt: str) -> str:
    client.beta.sessions.events.send(
        st.session_state.session_id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": prompt}]}],
        betas=BETAS,
    )
    response_text = ""
    with client.beta.sessions.events.stream(
        session_id=st.session_state.session_id,
        betas=BETAS,
    ) as stream:
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if block.type == "text":
                        response_text += block.text
            elif event.type == "session.status_idle":
                break
    return response_text

# ── Dataset Explorer ──────────────────────────────────────────────────────────
with st.expander("📊 Dataset Explorer", expanded=False):

    # -- Top-level metrics (load once per session) ----------------------------
    if "explorer_overall" not in st.session_state:
        with st.spinner("Loading dataset summary..."):
            raw = query_agent(
                "Query the Supabase `overall` table and return ALL rows as a JSON array. "
                "Each object must have keys: dataset, archived_on, n, n_id, n_id_distinct. "
                "Return ONLY the JSON array, no explanation, no markdown."
            )
            try:
                # strip any accidental markdown fences
                clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                st.session_state.explorer_overall = json.loads(clean)
            except Exception:
                st.session_state.explorer_overall = []

    overall_data = st.session_state.explorer_overall

    if overall_data:
        def fmt(n):
            try:
                n = int(n)
                if n >= 1_000_000_000: return f"{n/1e9:.1f}B"
                if n >= 1_000_000:     return f"{n/1e6:.1f}M"
                if n >= 1_000:         return f"{n/1e3:.1f}K"
                return str(n)
            except Exception:
                return str(n)

        n_datasets    = len({r["dataset"] for r in overall_data})
        latest_batch  = max((r.get("archived_on") or "") for r in overall_data)
        total_records = sum(int(r["n"]) for r in overall_data if r.get("n") not in (None, ""))

        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-card"><div class="val">{n_datasets}</div><div class="lbl">Datasets provisioned</div></div>
          <div class="metric-card"><div class="val">{fmt(total_records)}</div><div class="lbl">Total records (all datasets)</div></div>
          <div class="metric-card"><div class="val">{latest_batch}</div><div class="lbl">Latest batch</div></div>
        </div>
        """, unsafe_allow_html=True)

        # -- Dataset selector -------------------------------------------------
        all_datasets = sorted({r["dataset"] for r in overall_data})
        selected = st.selectbox("Select a dataset", all_datasets, key="ds_select")

        if selected:
            ds_rows = [r for r in overall_data if r["dataset"] == selected]
            latest  = sorted(ds_rows, key=lambda r: r.get("archived_on") or "", reverse=True)[0]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total records",    fmt(latest.get("n") or 0))
            col2.metric("Records with ID",  fmt(latest.get("n_id") or 0))
            col3.metric("Distinct patients", str(latest.get("n_id_distinct") or "—"))

            tab1, tab2 = st.tabs(["📈 Coverage over time", "✅ Column completeness"])

            # Coverage tab
            with tab1:
                cache_key = f"coverage_{selected}"
                if cache_key not in st.session_state:
                    with st.spinner(f"Loading coverage for {selected}..."):
                        raw = query_agent(
                            f"Query the Supabase `coverage` table WHERE dataset = '{selected}'. "
                            "Return ALL rows as a JSON array with keys: date_ym, n, n_id, archived_on. "
                            "Return ONLY the JSON array, no explanation, no markdown."
                        )
                        try:
                            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                            st.session_state[cache_key] = json.loads(clean)
                        except Exception:
                            st.session_state[cache_key] = []

                cov = st.session_state[cache_key]
                if cov:
                    import pandas as pd
                    df = pd.DataFrame(cov)
                    df["date_ym"] = pd.to_datetime(df["date_ym"], errors="coerce")
                    df = df.dropna(subset=["date_ym"]).sort_values("date_ym")
                    df["n"]    = pd.to_numeric(df["n"],    errors="coerce")
                    df["n_id"] = pd.to_numeric(df["n_id"], errors="coerce")
                    st.line_chart(df.set_index("date_ym")[["n", "n_id"]])
                else:
                    st.info("No coverage data available for this dataset.")

            # Completeness tab
            with tab2:
                cache_key2 = f"completeness_{selected}"
                if cache_key2 not in st.session_state:
                    with st.spinner(f"Loading completeness for {selected}..."):
                        raw = query_agent(
                            f"Query the Supabase `completeness` table WHERE dataset = '{selected}'. "
                            "Find the most recent archived_on value and return only rows for that batch. "
                            "Return as a JSON array with keys: column_name, completeness. "
                            "Return ONLY the JSON array, no explanation, no markdown."
                        )
                        try:
                            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                            st.session_state[cache_key2] = json.loads(clean)
                        except Exception:
                            st.session_state[cache_key2] = []

                comp = st.session_state[cache_key2]
                if comp:
                    import pandas as pd
                    df2 = pd.DataFrame(comp)
                    df2["completeness"] = pd.to_numeric(df2["completeness"], errors="coerce").round(3)
                    df2 = df2.sort_values("completeness", ascending=False)
                    st.dataframe(
                        df2.rename(columns={"column_name": "Column", "completeness": "Completeness"}),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No completeness data available for this dataset.")
    else:
        st.warning("Could not load dataset summary. The agent may still be initialising — try refreshing.")

st.divider()

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
                    tool_name  = getattr(event, "name", "unknown")
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
