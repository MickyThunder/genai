import random
from openai import AzureOpenAI
import configparser
import pyodbc
import pandas as pd
from graphviz import Digraph
import networkx as nx
import matplotlib.pyplot as plt
import os
from faker import Faker
import streamlit as st
config = configparser.ConfigParser()
config.read('config.ini')



api_base = config["AI"]["AZURE_OPENAI_ENDPOINT"]
api_key= config["AI"]["AZURE_OPENAI_API_KEY"]
deployment_name = config["AI"]["deployment_name"]
api_version = config["AI"]["api_version"] 

client = AzureOpenAI(
    api_key=api_key,  
    api_version=api_version,
    base_url=f"{api_base}/openai/deployments/{deployment_name}"
)



def call_ai_engineer(data):
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": f"Please review the Data Base Schema and provide your understanding, refer to this data \n{data}",
            },
        ],
    )
    return completion.choices[0].message.content
    

def connect_to_db():
    conn_str = f'''DRIVER={{{config[config["ENVIRONMENT"]["ENV"]]["DRIVER"]}}};
                SERVER={config[config["ENVIRONMENT"]["ENV"]]["SERVER"]};
                DATABASE={config[config["ENVIRONMENT"]["ENV"]]["DATABASE"]};Trusted_connection=yes;'''

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    return cursor

def getDataFrame(cursor,rows):
    """This method is used to get the data frame."""
    dataset = []
    for d in rows:
        dataset.append(tuple(d))
    columns = [col[0] for col in cursor.description]
    df = pd.DataFrame(dataset, columns=columns)
    return df
def get_schema_details(cursor):
    # Fetch table names
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo' and TABLE_NAME like '%DimProduct%' ")
    table_names = [row[0] for row in cursor]

    # Fetch column details for each table
    schema_details = {}
    for table_name in table_names:
        cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
        schema_details[table_name] = [row for row in cursor]
    return schema_details
    #conn.close()  # Close the database connection
    
def convert_sql_response_to_schema(sql_response):
    schema_lines = []

    for table_name, columns in sql_response.items():
        schema_lines.append(f"**Table:** {table_name}")
        schema_lines.append("| Column Name | Data Type |")
        schema_lines.append("|-------------|-----------|")
        for column_name, data_type in columns:
            schema_lines.append(f"| {column_name} | {data_type} |")
        schema_lines.append("")  # Add an empty line for better readability

    return "\n".join(schema_lines)

def get_table_schema(cursor,table_name):
    # Fetch column names and data types
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
    """)
    return cursor.fetchall()

def generate_test_data(cursor,table_name, num_rows=100):
    fake = Faker()
    schema = get_table_schema(cursor,table_name)
    test_data = {column: [] for column, _ in schema}

    for _ in range(num_rows):
        for column, data_type in schema:
            if data_type in ('int', 'smallint', 'tinyint'):
                test_data[column].append(random.randint(1, 100))  # Generate random integer
            elif data_type in ('float', 'decimal', 'money'):
                test_data[column].append(round(random.uniform(1.0, 100.0), 2))  # Generate random float
            elif data_type == 'varchar' or data_type == 'nvarchar':
                test_data[column].append(fake.sentence())  # Generate random string
            elif data_type == 'datetime':
                test_data[column].append(fake.date_time_this_year())  # Generate random datetime
            else:
                test_data[column].append(None)  # Default for unsupported types
    df = pd.DataFrame(test_data)
    #df.to_csv(f'../data/{table_name}.csv')
    st.chat_message("assistant").warning(f"Test data for table {table_name} have been created successfully!!! :+1: :tada:")
    st.download_button(
    label=f"Test data for table {table_name}",
    data=df.to_csv().encode("utf-8"),
    file_name=f"../data/{table_name}.csv",
    mime="text/csv",
)
    

relationshipDetails = {}
def get_db_relationship(cursor):
    query = f"""
            SELECT 
                fk.name AS FK_Name,
                tp.name AS Parent_Table,
                cp.name AS Parent_Column,
                tr.name AS Referenced_Table,
                cr.name AS Referenced_Column
            FROM 
                sys.foreign_keys AS fk
            INNER JOIN 
                sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN 
                sys.tables AS tp ON fkc.parent_object_id = tp.object_id
            INNER JOIN 
                sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            INNER JOIN 
                sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
            INNER JOIN 
                sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
            ORDER BY 
                tp.name, tr.name;
            """
    cursor.execute(query)
    rows = cursor.fetchall()
    df = getDataFrame(cursor,rows=rows)
    df.to_csv('../data/relationship.txt', sep='\t', index=False)
    df.to_pickle('../data/relationship.pkl')
    return df
cursor = connect_to_db()
#schema = get_schema_details(cursor=cursor)
#formated_schema = convert_sql_response_to_schema(schema)
#print (formated_schema)
rs = get_db_relationship(cursor=cursor)
print(rs)
# Get unique table names from Parent_Table and Referenced_Table
unique_tables = pd.Series(rs['Parent_Table'].tolist() + rs['Referenced_Table'].tolist()).unique()
unique_tables = [table.lower() for table in unique_tables]
unique_tables = sorted(unique_tables) 



def create_relationship_diagram(df=rs,table_name='DimProduct'):
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
    return dot

# Create the diagram
relationship_diagram = create_relationship_diagram(rs)

# Save and render the diagram
# Check if file relationship_diagram already exists, delete that file
if os.path.exists('relationship_diagram.png'):
    os.remove('relationship_diagram.png')
else:
    relationship_diagram.render('relationship_diagram', cleanup=True)





# Sidebar
""" with st.sidebar:
    st.markdown(
        "## How to use\n"
        "1. Enter your [OpenAI API key](https://platform.openai.com/account/api-keys) below🔑\n"  # noqa: E501
        "2. Upload a pdf, docx, or txt file📄\n"
        "3. Ask a question about the document💬\n"
    )
st.title("AI TechBA - Data Engineer Assistant")

# Chat Window
input_text = st.text_area("Enter your input text here:")

if st.button("Submit"):
    st.write("You entered:", input_text)
    st.write("AI response will be displayed here")
    st.image('relationship_diagram.png')
    input_text = input_text.replace('\n', ' ')"""
#ai_response = call_ai_engineer(rs)


#print(ai_response)

