import streamlit as st
import anthropic

# ── BHF brand styles ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  :root {
    --bhf-red:       #C8102E;
    --bhf-red-dark:  #8B0000;
    --bhf-red-light: #FDF0F2;
    --bhf-border:    #E8C0C7;
    --text-primary:  #1A1A1A;
    --text-muted:    #595959;
    --bg-page:       #FAFAFA;
  }

  /* Page background */
  .stApp { background-color: var(--bg-page); }

  /* Header */
  .bhf-header {
    background-color: var(--bhf-red);
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin-bottom: 1.25rem;
  }
  .bhf-header h1 {
    color: #ffffff !important;
    margin: 0 0 0.2rem;
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -0.01em;
  }
  .bhf-header p {
    color: rgba(255,255,255,0.88);
    margin: 0;
    font-size: 0.8rem;
  }

  /* Source card */
  .bhf-card {
    background: #ffffff;
    border: 1px solid var(--bhf-border);
    border-left: 4px solid var(--bhf-red);
    border-radius: 6px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: var(--text-primary);
  }
  .bhf-card strong { color: var(--text-primary); }

  /* Pills */
  .source-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.65rem; }
  .source-pill {
    background: #ffffff;
    border: 1.5px solid var(--bhf-red);
    color: var(--bhf-red-dark);
    border-radius: 20px;
    padding: 0.28rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 600;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    transition: background 0.15s, color 0.15s;
  }
  .source-pill:hover {
    background: var(--bhf-red);
    color: #ffffff;
    text-decoration: none;
  }
  .source-pill:focus {
    outline: 3px solid #005fcc;
    outline-offset: 2px;
  }

  /* Intro hint */
  .bhf-hint {
    background: var(--bhf-red-light);
    border: 1px solid var(--bhf-border);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: var(--text-primary);
    margin-bottom: 1rem;
    line-height: 1.55;
  }
  .bhf-hint code {
    background: #fff;
    border: 1px solid var(--bhf-border);
    border-radius: 3px;
    padding: 0.1rem 0.35rem;
    font-size: 0.8rem;
    color: var(--bhf-red-dark);
  }

  /* Expanders */
  details summary {
    color: var(--bhf-red-dark) !important;
    font-weight: 600;
  }

  /* Links inside chat */
  div[data-testid="stChatMessage"] a {
    color: var(--bhf-red-dark);
    text-decoration: underline;
  }

  /* Chat input border accent */
  div[data-testid="stChatInput"] textarea:focus {
    border-color: var(--bhf-red) !important;
    box-shadow: 0 0 0 2px rgba(200,16,46,0.2) !important;
  }

  /* Divider */
  hr { border-color: var(--bhf-border); }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="bhf-header" role="banner">
  <h1>❤️ BHF DSC Assistant</h1>
  <p>BHF Data Science Centre · HDR UK · NHS England SDE</p>
</div>
""", unsafe_allow_html=True)

# ── Source pills ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="bhf-card" role="complementary" aria-label="Available sources">
  <strong>Sources available to this assistant</strong>
  <div class="source-row">
    <a class="source-pill" href="https://github.com/BHFDSC/documentation"
       target="_blank" rel="noopener" aria-label="BHFDSC documentation on GitHub (opens in new tab)">
      📄 BHFDSC/documentation
    </a>
    <a class="source-pill" href="https://github.com/BHFDSC/standard-pipeline"
       target="_blank" rel="noopener" aria-label="BHFDSC standard pipeline on GitHub (opens in new tab)">
      ⚙️ BHFDSC/standard-pipeline
    </a>
    <a class="source-pill" href="https://bhfdatasciencecentre.org/dashboard/"
       target="_blank" rel="noopener" aria-label="Dataset Summary Dashboard (opens in new tab)">
      📊 Dataset Summary Dashboard
    </a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Prompt suggestions ────────────────────────────────────────────────────────
st.markdown("""
<div class="bhf-hint" role="note" aria-label="Example questions">
  <strong>Try asking:</strong><br>
  <code>How do I load the latest demographics table in PySpark?</code> &nbsp;·&nbsp;
  <code>What datasets are available and what are their record counts?</code> &nbsp;·&nbsp;
  <code>What changed in the last batch update?</code> &nbsp;·&nbsp;
  <code>Show me column completeness for hes_apc</code>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Anthropic client & session ────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
AGENT_ID       = st.secrets["AGENT_ID"]
ENVIRONMENT_ID = st.secrets["ENVIRONMENT_ID"]
VAULT_ID       = st.secrets["VAULT_ID"]
BETAS          = ["managed-agents-2026-04-01"]

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
