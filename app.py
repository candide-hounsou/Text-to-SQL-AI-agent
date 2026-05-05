import streamlit as st
import pandas as pd
import uuid
import os
import plotly.express as px

try:
    from agent import create_graph
    from langchain_core.messages import HumanMessage
except ModuleNotFoundError as exc:
    st.set_page_config(page_title="Olist Data Agent", page_icon="🤖", layout="wide")
    st.title("🤖 Olist Text-to-SQL Agent")
    st.error(
        f"Missing Python dependency: {exc.name}. Install the project requirements in the active virtual environment and rerun the app."
    )
    st.code("python -m pip install -r requirements.txt\nstreamlit run app.py", language="bash")
    st.stop()

from src.llm.factory import PROVIDER_MODELS, LLMProvider

st.set_page_config(page_title="Olist Data Agent", page_icon="🤖", layout="wide")
st.title("🤖 Olist Text-to-SQL Agent")
st.markdown("Ask me anything about the Olist e-commerce database! I can write SQL, execute it, self-correct errors, and analyze the results.")

# ---------------------------------------------------------------------------
# Sidebar — Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    # --- LLM Settings ---
    st.subheader("🧠 LLM Settings")
    provider_labels = {"OpenAI": "openai", "Anthropic": "anthropic", "Gemini": "gemini"}
    provider_label = st.selectbox("LLM Provider", options=list(provider_labels.keys()), index=0)
    provider = provider_labels[provider_label]

    provider_enum = LLMProvider(provider)
    model_options = PROVIDER_MODELS[provider_enum]
    model_name = st.selectbox("Model", options=model_options, index=0)

    st.markdown("---")

    # --- RAG Settings ---
    st.subheader("🔍 Schema Retrieval")
    use_rag = st.toggle("Enable RAG Schema Linking", value=True,
                        help="Use TF-IDF retrieval to inject only relevant schema tables into the prompt.")

    st.markdown("---")

    # --- Database Connection ---
    st.subheader("🗄️ Database Connection")
    db_source = st.selectbox(
        "Data Source",
        options=["Built-in (Olist)", "Upload SQLite / CSV", "Connection String (PostgreSQL / MySQL)"],
    )

    connector = None  # resolved below

    if db_source == "Upload SQLite / CSV":
        uploaded_file = st.file_uploader("Upload a .db or .csv file", type=["db", "csv"])
        if uploaded_file is not None:
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            if file_ext == ".csv":
                from src.connectors.csv_connector import CSVConnector
                connector = CSVConnector(uploaded_file.read(), table_name="data")
                st.success(f"✅ CSV loaded as table 'data'")
            elif file_ext == ".db":
                upload_dir = "data/uploads"
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, uploaded_file.name)
                with open(save_path, "wb") as fh:
                    fh.write(uploaded_file.read())
                from src.connectors.sqlite import SQLiteConnector
                connector = SQLiteConnector(save_path)
                st.success(f"✅ SQLite database loaded: {uploaded_file.name}")

    elif db_source == "Connection String (PostgreSQL / MySQL)":
        db_engine = st.selectbox("Engine", ["PostgreSQL", "MySQL"])
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Host", value="localhost")
            dbname = st.text_input("Database", value="")
            user = st.text_input("User", value="")
        with col2:
            default_port = 5432 if db_engine == "PostgreSQL" else 3306
            port = st.number_input("Port", value=default_port, step=1)
            password = st.text_input("Password", type="password")

        if st.button("Connect"):
            try:
                if db_engine == "PostgreSQL":
                    from src.connectors.postgresql import PostgreSQLConnector
                    conn_obj = PostgreSQLConnector(
                        host=host, port=int(port), dbname=dbname, user=user, password=password
                    )
                else:
                    from src.connectors.mysql import MySQLConnector
                    conn_obj = MySQLConnector(
                        host=host, port=int(port), database=dbname, user=user, password=password
                    )
                conn_obj.connect()
                st.session_state.connector = conn_obj
                st.success(f"✅ Connected to {db_engine}!")
            except Exception as e:
                st.error(f"Connection failed: {e}")

        if "connector" in st.session_state and st.session_state.connector is not None:
            connector = st.session_state.connector

# Store the active connector (None means default SQLite)
if connector is not None:
    st.session_state.connector = connector

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "agent_graph" not in st.session_state:
    st.session_state.agent_graph = create_graph()

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Display conversation history
# ---------------------------------------------------------------------------
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("dataframe") is not None and not msg["dataframe"].empty:
            df = msg["dataframe"]
            c_type = msg.get("chart_type", "none")

            with st.expander("📊 View Raw Data", expanded=False):
                st.dataframe(df, use_container_width=True)

            if c_type != "none" and len(df) > 1 and len(df.columns) >= 2:
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

                if numeric_cols and categorical_cols:
                    x_col = categorical_cols[0]
                    y_col = numeric_cols[0]

                    if c_type == "bar":
                        fig = px.bar(df, x=x_col, y=y_col, color=x_col, text_auto=".2s", template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True, key=f"hist_bar_{i}")
                    elif c_type == "pie":
                        fig = px.pie(df, names=x_col, values=y_col, template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True, key=f"hist_pie_{i}")
                    elif c_type == "line":
                        plot_df = df.sort_values(by=x_col)
                        fig = px.line(plot_df, x=x_col, y=y_col, markers=True, template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True, key=f"hist_line_{i}")

# ---------------------------------------------------------------------------
# Chat Input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ex: What are the top 5 product categories by revenue?"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status = st.status("🧠 Agent is thinking...", expanded=True)

        initial_state = {
            "query": prompt,
            "messages": [HumanMessage(content=prompt)],
        }

        active_connector = st.session_state.get("connector")

        config = {
            "configurable": {
                "thread_id": st.session_state.thread_id,
                "provider": provider,
                "model_name": model_name,
                "use_rag": use_rag,
                "connector": active_connector,
            }
        }

        final_summary = ""
        final_df = None
        chart_type = "none"

        for event in st.session_state.agent_graph.stream(initial_state, config=config):
            for node_name, node_state in event.items():

                if node_name == "reformulate_query":
                    status.write("⏳ Reformulation de la question...")

                elif node_name == "classify_query":
                    complexity = node_state.get("query_complexity")
                    reason = node_state.get("classification_reason")

                    if complexity == "out_of_scope":
                        status.error(f"❌ Requête hors périmètre : {reason}")
                        final_summary = reason
                    elif complexity == "complex":
                        status.warning("🧠 Requête complexe détectée. Activation de l'architecte SQL...")
                    else:
                        status.success("✅ Requête simple détectée. Traitement direct...")

                elif node_name == "plan_sql_query":
                    status.write("⏳ Élaboration du plan de jointure (Chain-of-Thought)...")
                    with st.expander("📋 Voir le plan d'exécution", expanded=False):
                        st.markdown(node_state.get("sql_plan"))

                elif node_name == "generate_sql":
                    status.write("⏳ Traduction en SQL...")
                    with st.expander("🔍 View Generated SQL", expanded=False):
                        st.code(node_state.get("sql_query"), language="sql")

                elif node_name == "execute_sql":
                    error = node_state.get("error")
                    if error:
                        retries = node_state.get("retry_count", 1)
                        if retries >= 3:
                            status.error(f"❌ Échec définitif après 3 tentatives de correction ({error}).")
                        else:
                            status.warning(f"⚠️ Erreur SQL : {error}. Tentative de correction automatique ({retries}/3)...")
                    else:
                        status.write("✅ Exécution réussie sur la base de données !")
                        raw_data = node_state.get("raw_data", [])
                        if raw_data:
                            final_df = pd.DataFrame(raw_data)
                            with st.expander("📊 View Raw Data", expanded=False):
                                st.dataframe(final_df, use_container_width=True)

                elif node_name == "summarize_results":
                    status.write("⏳ Synthèse de la réponse et choix du graphique...")
                    final_summary = node_state.get("summary")
                    chart_type = node_state.get("chart_type", "none")

        status.update(label="✅ Task Completed!", state="complete", expanded=False)

        if final_summary:
            st.markdown(final_summary)

        if final_df is not None and not final_df.empty:
            with st.expander("📊 View Raw Data", expanded=False):
                st.dataframe(final_df, use_container_width=True)

            csv_data = final_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Data (CSV)",
                data=csv_data,
                file_name="olist_export.csv",
                mime="text/csv",
                key=f"dl_{len(st.session_state.messages)}",
            )

            if chart_type != "none" and len(final_df) > 1 and len(final_df.columns) >= 2:
                numeric_cols = final_df.select_dtypes(include=["number"]).columns.tolist()
                categorical_cols = final_df.select_dtypes(exclude=["number"]).columns.tolist()
                if numeric_cols and categorical_cols:
                    x_col = categorical_cols[0]
                    y_col = numeric_cols[0]
                    st.markdown(f"📊 **Visualization ({chart_type.upper()}): {y_col} by {x_col}**")
                    if chart_type == "bar":
                        fig = px.bar(final_df, x=x_col, y=y_col, color=x_col, text_auto=".2s", template="plotly_dark")
                    elif chart_type == "pie":
                        fig = px.pie(final_df, names=x_col, values=y_col, template="plotly_dark")
                    elif chart_type == "line":
                        plot_df = final_df.sort_values(by=x_col)
                        fig = px.line(plot_df, x=x_col, y=y_col, markers=True, template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_summary,
            "dataframe": final_df,
            "chart_type": chart_type,
        })
