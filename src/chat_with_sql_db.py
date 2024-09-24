import configparser
from openai import AzureOpenAI
import streamlit as st
from pathlib import Path
from langchain.llms.openai import OpenAI
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
import azai
from sqlalchemy.engine import URL
from langchain.llms import BaseLanguageModel


# Read configuration
config = configparser.ConfigParser()
config.read('config.ini')

api_base = config["AI"]["AZURE_OPENAI_ENDPOINT"]
api_key = config["AI"]["AZURE_OPENAI_API_KEY"]
deployment_name = config["AI"]["deployment_name"]
api_version = config["AI"]["api_version"]  # this might change in the future
# Wrapper class to ensure AzureOpenAI is recognized as a subclass of BaseLanguageModel
class AzureOpenAIWrapper(BaseLanguageModel):
    def __init__(self, api_key, api_version, base_url):
        self.azure_openai = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            base_url=base_url
        )

    # Implement necessary methods to interact with Azure OpenAI
    def generate(self, prompt):
        # Example method to generate text using Azure OpenAI
        return self.azure_openai.generate(prompt)
# Initialize AzureOpenAI client
llm = AzureOpenAIWrapper(
    api_key=api_key,
    api_version=api_version,
    base_url=f"{api_base}/openai/deployments/{deployment_name}"
)
st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
st.title("🦜 LangChain: Chat with SQL DB")

INJECTION_WARNING = """
                    SQL agent can be vulnerable to prompt injection. Use a DB role with limited permissions.
                    Read more [here](https://python.langchain.com/docs/security).
                    """
LOCALDB = "USE_LOCALDB"

# User inputs
radio_opt = ["Use sample database - Chinook.db", "Connect to your SQL database"]
selected_opt = st.sidebar.radio(label="Choose suitable option", options=radio_opt)
if radio_opt.index(selected_opt) == 1:
    st.sidebar.warning(INJECTION_WARNING, icon="⚠️")
    db_uri = st.sidebar.text_input(
        label="Database URI", placeholder="mysql://user:pass@hostname:port/db"
    )
else:
    db_uri = LOCALDB

openai_api_key = st.sidebar.text_input(
    label="OpenAI API Key",
    type="password",
)

# Check user inputs
if not db_uri:
    st.info("Please enter database URI to connect to your database.")
    st.stop()



# Setup agent
#llm = OpenAI(openai_api_key=openai_api_key, temperature=0, streaming=True)
#llm = azai.client

@st.cache_resource(ttl="2h")
def configure_db(db_uri):
    if db_uri == "LOCALDB":
        # Make the DB connection read-only to reduce risk of injection attacks
        # See: https://python.langchain.com/docs/security
        db_filepath = (Path(__file__).parent / "Chinook.db").absolute()
        creator = lambda: sqlite3.connect(f"file:{db_filepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    else:
        # Connect to SQL Server using pyodbc
        connection_string = URL.create(
            "mssql+pyodbc",
            query={
                "odbc_connect": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_uri.split('/')[0]};DATABASE={db_uri.split('/')[1]};Trusted_Connection=yes;"
            }
        )
        engine = create_engine(connection_string)
        return SQLDatabase(engine)
#SERVER = L3163213\MYLOCAL
#DATABASE = AdventureWorksDW2022
# Replace 'your_sql_server_connection_string' with your actual SQL Server connection string
db_uri = "L3163213\\MYLOCAL/AdventureWorksDW2022"
db = configure_db(db_uri)

#db.run_query("SELECT 1")  # Check if the connection
#db = azai.connect_to_db()

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input(placeholder="Ask me anything!")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container())
        response = agent.run(user_query, callbacks=[st_cb])
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write(response)
