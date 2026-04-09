import streamlit as st
import anthropic

client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
AGENT_ID = st.secrets["AGENT_ID"]
ENVIRONMENT_ID = st.secrets["ENVIRONMENT_ID"]
VAULT_ID = st.secrets["VAULT_ID"]
BETAS = ["managed-agents-2026-04-01"]

st.title("BHF DSC Assistant")
st.markdown("""Use natural languate to search \n 
            [bhf hds docs](https://bhfdsc.github.io/documentation/) \n 
            [bhf standard pipeline](https://github.com/BHFDSC/standard-pipeline/) \n 
            [bhf data summary dashboard](https://bhfdatasciencecentre.org/dashboard/)
           """)

# Create a session once per Streamlit session
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

# Display chat history
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

# Chat input
if prompt := st.chat_input("Ask about BHF DSC..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "steps": []})
    with st.chat_message("user"):
        st.write(prompt)

    # Send message to agent
    client.beta.sessions.events.send(
        st.session_state.session_id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": prompt}]}],
        betas=BETAS,
    )

    # Stream the response
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
