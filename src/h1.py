
import pyodbc

import google.generativeai as genai
import configparser
from prompts import prompts

config = configparser.ConfigParser()
config.read('config.ini')
# Set up your API key
genai.configure(api_key=config["AI"]["GEMINI_API_KEY"])
# --- Configuration ---
generation_config = {

    #"max_output_tokens": 8192,
    #"response_mime_type": "text/plain",
}

model = genai.GenerativeModel("gemini-1.5-flash", generation_config)
# --- Database Connection ---
# Replace with your SQL Server connection details

conn_str = f'''DRIVER={{{config[config["ENVIRONMENT"]["ENV"]]["DRIVER"]}}};
            SERVER={config[config["ENVIRONMENT"]["ENV"]]["SERVER"]};
            DATABASE={config[config["ENVIRONMENT"]["ENV"]]["DATABASE"]};Trusted_connection=yes;'''

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()





# Example usage for database schema analysis
def call_ai_engineer(data, prompt):
  """Sends schema text and prompt to Gemini API for analysis."""
  response = model.generate_content([prompt,data]) 
  print(response)
  return response

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
# --- Fetch Schema Details ---
# Fetch table names
cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo'")
table_names = [row[0] for row in cursor]

# Fetch column details for each table
schema_details = {}
for table_name in table_names:
    cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
    schema_details[table_name] = [row for row in cursor]

conn.close()  # Close the database connection
print(schema_details)
schema_text = convert_sql_response_to_schema(schema_details)
print(schema_text)
gemini_analysis = call_ai_engineer("How to create a database?",prompts["Data Modeler"])

#print(gemini_analysis)