import json
from graphviz import Digraph
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import ChatMessage
from langchain_openai import ChatOpenAI
import streamlit as st
from openai import AzureOpenAI
import configparser
import azai 
config = configparser.ConfigParser()
config.read('config.ini')





llm = azai.client
class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

azai.cursor.execute("SELECT DB_NAME()")
database_name = azai.cursor.fetchone()[0]

def create_relationship_diagram7(df=azai.rs,table_name="DimProduct"):
    relationship_diagram = azai.create_relationship_diagram(df, table_name)
    st.image('relationship_diagram.png')
    
def create_relationship_diagram(table_name='DimProduct'):
    df = azai.rs
    # check table name exist in database
    if table_name not in df.Referenced_Table.values and table_name not in df.Parent_Table.values:
        raise Exception("Table name not found in the database schema.")
        
    dot = Digraph(format='png')
    df = df[(df.Referenced_Table==table_name) | (df.Parent_Table==table_name)]
    # Set graph size
    dot.attr(size='10,80')  # Change size as needed
    dot.attr(dpi='500')      # Higher DPI for better quality

    # Add nodes and edges based on the DataFrame
    for _, row in df.iterrows():
        # Add parent and referenced tables as nodes
        dot.node(row['Referenced_Table'], row['Referenced_Table'], style="filled", fillcolor="lightblue", fontsize='12')
        dot.node(row['Parent_Table'], row['Parent_Table'], style="filled", fillcolor="lightgreen", fontsize='12')

        # Add an edge representing the foreign key relationship
        dot.edge(row['Referenced_Table'], row['Parent_Table'], label=row['FK_Name'], fontsize='10')
    dot.render('relationship_diagram', cleanup=True)
    st.image('relationship_diagram.png')
    return dot

st.title("AI Tech BA - Assistant :rocket:")
st.write(f"Connected to Database: :blue[{database_name}] :sunglasses:" )

st.divider()
# Custom CSS to change the sidebar background color
st.html(
    """
<style>
[data-testid="stSidebarContent"] {
    color: white;
    background-color: #262730;
},
[data-testid="stMarkdownContainer"] {
    color: white;
},
[data-testid="stChatMessage"] {
    color: black;
},

</style>
"""
)


with st.sidebar:
    st.markdown("""<span style='color: white;font-size:25px'>AI Tech BA - Assistant</span>""", unsafe_allow_html=True)
    st.markdown("1. Use AI Tech BA, by asking database related questions")
 
    st.markdown("2. You are connected to the Database Schema Assistant")
    st.markdown("3. Ask a question about the database schema")
    st.markdown("4. The AI will provide you with the answer")

if "messages" not in st.session_state:
    st.session_state["messages"] = [ChatMessage(role="assistant", content="How can I help you? :pray:")]
    #st.session_state["messages"] = [ChatMessage(role="assistant", content="Here is the dataframe "+azai.rs.to_csv(index=False))]
    #messages.append({"role": "user", "content": f"Here is the dataframe:\n"})
    #st.session_state["messages"] = [ChatMessage(role="assistant", content="Please provide me with the database schema")]

for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

if prompt := st.chat_input():
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    st.chat_message("user").write(prompt)

   
        
    # Convert ChatMessage objects to dictionaries
    messages = [{"role": msg.role, "content": msg.content} for msg in st.session_state.messages]
    #messages = st.session_state.messages
    # Add dataframe content as a new message
    #messages.append({"role": "user", "content": f"Here is the dataframe:\n {azai.rs.to_csv(index=False)}"})
    tools = [
        {   "type": "function",
            "function": {
                "name": "create_relationship_diagram",
                "description": "A function that creates a relationship diagram from a dataframe for a given table name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string",
                                        "description": "When a customer requests a relationship diagram for the table DimProduct, the table_name is set to DimProduct."
                                        }
                    },
                    "required": ["table_name"]
                }
            }
            }
        ]
    response = llm.chat.completions.create(
    model="gpt-4",
        messages=messages,
        stream=False,
        tools=tools,
        tool_choice="auto"
    )
    print(response.choices[0].message)
    #st.session_state.messages.append(ChatMessage(role="assistant", content=response.choices[0].message.content))
    #messages.append({"role": "assistant", "content": response.choices[0].message.content})
    #return completion.choices[0].message.content
    #response = llm.invoke(st.session_state.messages, stream=True, callbacks=[stream_handler])
    #response = llm.invoke(st.session_state.messages)
    assistant_message = ""
    assistant_message = response.choices[0].message.content
    if hasattr(response.choices[0].message, 'content') and response.choices[0].message.content:
            assistant_message = response.choices[0].message.content
            print("hello",response.choices[0].message.content)
            #st.session_state.messages.append(ChatMessage(role="assistant", content=assistant_message))
            #messages.append({"role": "assistant", "content": assistant_message})
            #stream_handler.on_llm_new_token(assistant_message)

    # Handle function calls
    if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "create_relationship_diagram":
                try:
                    if tool_call.function.arguments:
                        function_args = json.loads(tool_call.function.arguments)
                        print(f"Function arguments: {function_args}")
                        create_relationship_diagram(function_args.get("table_name"))
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": "create_relationship_diagram",
                            "content": "Relationship diagram created successfully.",
                        })
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError: {e}")
                except Exception as e:
                    assistant_message = f"Error: {e}"
                    #st.session_state.messages.append(ChatMessage(role="assistant", content=f"Error: {e}"))
                    print(f"Error: {e}")
    else:
        print("No tool calls were made by the model.")
    # Second API call: Get the final response from the model
    #final_response = llm.chat.completions.create(
        #   model="gpt-4",
        #  messages=messages,
    #) 
    if assistant_message:
        print(assistant_message)
        st.session_state.messages.append(ChatMessage(role="assistant", content=assistant_message))
        st.chat_message("assistant").write(assistant_message)
    else:
        print("Assistant message is None.")