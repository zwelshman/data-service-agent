import streamlit as st
import anthropic
import time

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
    --bg-page:       #F8F8F8;
    --bg-white:      #FFFFFF;
  }

  .stApp { background-color: var(--bg-page); }

  /* ── Header ── */
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
  }
  .bhf-header p { color: rgba(255,255,255,0.88); margin: 0; font-size: 0.8rem; }

  /* ── Source card ── */
  .bhf-card {
    background: var(--bg-white);
    border: 1px solid var(--bhf-border);
    border-left: 4px solid var(--bhf-red);
    border-radius: 6px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: var(--text-primary);
  }

  /* ── Pills ── */
  .source-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.65rem; }
  .source-pill {
    background: var(--bg-white);
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
  }
  .source-pill:hover { background: var(--bhf-red); color: #ffffff; text-decoration: none; }
  .source-pill:focus { outline: 3px solid #005fcc; outline-offset: 2px; }

  /* ── Hint bar ── */
  .bhf-hint {
    background: var(--bhf-red-light);
    border: 1px solid var(--bhf-border);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: var(--text-primary);
    margin-bottom: 1rem;
    line-height: 1.6;
  }
  .bhf-hint code {
    background: var(--bg-white);
    border: 1px solid var(--bhf-border);
    border-radius: 3px;
    padding: 0.1rem 0.35rem;
    font-size: 0.8rem;
    color: var(--bhf-red-dark);
  }

  /* ── Activity log items ── */
  .activity-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.45rem 0.65rem;
    border-radius: 6px;
    margin-bottom: 0.3rem;
    font-size: 0.84rem;
    color: var(--text-primary);
    background: var(--bg-white);
    border: 1px solid #eeeeee;
  }
  .activity-item.thinking {
    background: #FFF8E1;
    border-color: #FFE082;
  }
  .activity-item.tool {
    background: #E8F4FD;
    border-color: #90CAF9;
  }
  .activity-item.result {
    background: #E8F5E9;
    border-color: #A5D6A7;
  }
  .activity-item.agent {
    background: var(--bhf-red-light);
    border-color: var(--bhf-border);
  }
  .activity-icon { font-size: 1rem; flex-shrink: 0; margin-top: 1px; }
  .activity-text { flex: 1; line-height: 1.45; color: var(--text-primary); }
  .activity-text strong { color: var(--text-primary); }
  .activity-elapsed {
    font-size: 0.72rem;
    color: var(--text-muted);
    white-space: nowrap;
    margin-top: 2px;
  }

  /* ── Chat messages — force readable colours ── */
  div[data-testid="stChatMessage"] {
    background: var(--bg-white) !important;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    color: var(--text-primary) !important;
  }
  div[data-testid="stChatMessage"] p,
  div[data-testid="stChatMessage"] li,
  div[data-testid="stChatMessage"] td,
  div[data-testid="stChatMessage"] th,
  div[data-testid="stChatMessage"] span,
  div[data-testid="stChatMessage"] div {
    color: var(--text-primary) !important;
  }
  div[data-testid="stChatMessage"] a {
    color: var(--bhf-red-dark) !important;
    text-decoration: underline;
  }
  div[data-testid="stChatMessage"] code {
    background: #F3F3F3;
    color: var(--text-primary) !important;
    border-radius: 3px;
    padding: 0.1rem 0.3rem;
  }
  div[data-testid="stChatMessage"] pre {
    background: #F3F3F3 !important;
    color: var(--text-primary) !important;
    border-radius: 6px;
    padding: 0.75rem;
  }

  /* ── Chat input ── */
  div[data-testid="stChatInput"] textarea {
    background: var(--bg-white) !important;
    color: var(--text-primary) !important;
  }
  div[data-testid="stChatInput"] textarea:focus {
    border-color: var(--bhf-red) !important;
    box-shadow: 0 0 0 2px rgba(200,16,46,0.18) !important;
  }

  hr { border-color: var(--bhf-border); }
  details summary { color: var(--bhf-red-dark) !important; font-weight: 600; }
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

# ── Hint bar ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="bhf-hint" role="note">
  <strong>Try asking:</strong><br>
  <code>How do I load the latest demographics table in PySpark?</code> &nbsp;·&nbsp;
  <code>What datasets are available and their record counts?</code> &nbsp;·&nbsp;
  <code>Show me column completeness for hes_apc</code> &nbsp;·&nbsp;
  <code>What changed in the last batch update?</code>
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{int(seconds//60)}m {int(seconds%60)}s"

def render_activity(icon: str, css_class: str, label: str, detail: str, elapsed: float):
    detail_html = f"<br><span style='color:#595959;font-size:0.78rem'>{detail}</span>" if detail else ""
    return f"""
    <div class="activity-item {css_class}" role="status" aria-label="{label}">
      <span class="activity-icon" aria-hidden="true">{icon}</span>
      <span class="activity-text"><strong>{label}</strong>{detail_html}</span>
      <span class="activity-elapsed">{fmt_elapsed(elapsed)}</span>
    </div>"""

# ── Replay stored messages ────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Replay activity log for assistant turns
        if msg["role"] == "assistant" and msg.get("activity"):
            with st.expander("🔍 Agent activity", expanded=False):
                html = ""
                for act in msg["activity"]:
                    html += render_activity(
                        act["icon"], act["css"], act["label"],
                        act.get("detail", ""), act["elapsed"]
                    )
                st.markdown(html, unsafe_allow_html=True)
        if msg["content"]:
            st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about datasets, pipelines, phenotypes, codelists..."):

    st.session_state.messages.append({"role": "user", "content": prompt, "activity": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    client.beta.sessions.events.send(
        st.session_state.session_id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": prompt}]}],
        betas=BETAS,
    )

    with st.chat_message("assistant"):

        # Live activity log placeholder (shown while streaming)
        activity_placeholder = st.empty()
        response_placeholder = st.empty()

        activity_log  = []   # list of dicts for storage + replay
        response_text = ""
        turn_start    = time.time()

        def redraw_activity():
            html = ""
            for act in activity_log:
                html += render_activity(
                    act["icon"], act["css"], act["label"],
                    act.get("detail", ""), act["elapsed"]
                )
            activity_placeholder.markdown(html, unsafe_allow_html=True)

        def add_activity(icon, css, label, detail=""):
            activity_log.append({
                "icon": icon, "css": css,
                "label": label, "detail": detail,
                "elapsed": time.time() - turn_start,
            })
            redraw_activity()

        # Initial "thinking" state
        add_activity("🧠", "thinking", "Agent is thinking…")

        with client.beta.sessions.events.stream(
            session_id=st.session_state.session_id,
            betas=BETAS,
        ) as stream:
            for event in stream:

                if event.type == "agent.thinking":
                    thinking = getattr(event, "thinking", "").strip()
                    # Replace the generic thinking entry with actual content
                    if activity_log and activity_log[-1]["label"] == "Agent is thinking…":
                        activity_log.pop()
                    preview = (thinking[:120] + "…") if len(thinking) > 120 else thinking
                    add_activity("🧠", "thinking", "Thinking", preview)

                elif event.type == "agent.tool_use":
                    tool_name  = getattr(event, "name", "unknown")
                    tool_input = getattr(event, "input", {})
                    # Friendly label for common tools
                    friendly = {
                        "list_projects":  "Listing Supabase projects",
                        "list_tables":    "Inspecting database tables",
                        "execute_sql":    "Running SQL query",
                        "list_organizations": "Listing organisations",
                    }.get(tool_name, f"Using tool: {tool_name}")
                    detail = ""
                    if isinstance(tool_input, dict) and "query" in tool_input:
                        q = tool_input["query"].strip().replace("\n", " ")
                        detail = (q[:100] + "…") if len(q) > 100 else q
                    add_activity("🔧", "tool", friendly, detail)

                elif event.type == "agent.tool_result":
                    tool_name = getattr(event, "name", "unknown")
                    raw = getattr(event, "content", "") or getattr(event, "output", "")
                    result_str = raw if isinstance(raw, str) else " ".join(
                        getattr(b, "text", "") for b in raw
                    )
                    is_error = "error" in result_str.lower()[:60]
                    if is_error:
                        add_activity("❌", "result", f"Tool error — retrying…", "")
                    else:
                        rows = result_str.count("{")
                        detail = f"{rows} row(s) returned" if rows else ""
                        add_activity("✅", "result", "Got result", detail)

                elif event.type == "agent.message":
                    # Agent narrating between tool calls — add as activity entry
                    interim = ""
                    for block in event.content:
                        if block.type == "text":
                            interim += block.text
                    if interim.strip():
                        preview = (interim.strip()[:120] + "…") if len(interim.strip()) > 120 else interim.strip()
                        add_activity("💬", "agent", "Agent", preview)
                    # Accumulate for final response
                    response_text += interim

                elif event.type == "session.status_idle":
                    break

        # Collapse activity log into expander, show final answer cleanly
        activity_placeholder.empty()
        if activity_log:
            with st.expander(f"🔍 Agent activity ({fmt_elapsed(time.time() - turn_start)})", expanded=False):
                html = ""
                for act in activity_log:
                    html += render_activity(
                        act["icon"], act["css"], act["label"],
                        act.get("detail", ""), act["elapsed"]
                    )
                st.markdown(html, unsafe_allow_html=True)

        response_placeholder.markdown(response_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "activity": activity_log,
    })
