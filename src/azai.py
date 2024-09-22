from openai import AzureOpenAI
import configparser
import pyodbc
import pandas as pd
config = configparser.ConfigParser()
config.read('config.ini')



api_base = config["AI"]["AZURE_OPENAI_ENDPOINT"]
api_key= config["AI"]["AZURE_OPENAI_API_KEY"]
deployment_name = config["AI"]["deployment_name"]
api_version = config["AI"]["api_version"] # this might change in the future

client = AzureOpenAI(
    api_key=api_key,  
    api_version=api_version,
    base_url=f"{api_base}/openai/deployments/{deployment_name}"
)

print(vars(client))


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
    
    return df
cursor = connect_to_db()
schema = get_schema_details(cursor=cursor)
formated_schema = convert_sql_response_to_schema(schema)
#print (formated_schema)
rs = get_db_relationship(cursor=cursor)
print(rs)
ai_response = call_ai_engineer(rs)


print(ai_response)