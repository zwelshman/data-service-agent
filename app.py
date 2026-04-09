import streamlit as st
import anthropic

client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

AGENT_ID = st.secrets["AGENT_ID"]
ENVIRONMENT_ID = st.secrets["ENVIRONMENT_ID"]
VAULT_ID = st.secrets["VAULT_ID"]

BETAS = ["managed-agents-2026-04-01"]

st.title("BHF DSC Assistant")

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
        st.write(msg["content"])

# Chat input
if prompt := st.chat_input("Ask about BHF DSC..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
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
        placeholder = st.empty()
        with client.beta.sessions.events.stream(
            session_id=st.session_state.session_id,
            betas=BETAS,
        ) as stream:
            for event in stream:
                if event.type == "agent.message":
                    for block in event.content:
                        if block.type == "text":
                            response_text += block.text
                            placeholder.write(response_text)
                elif event.type == "session.status_idle":
                    break  # agent finished its turn

    st.session_state.messages.append({"role": "assistant", "content": response_text})
