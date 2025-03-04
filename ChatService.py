#Chat with Database
# Install required libraries
!pip install -q google-generativeai sqlite3 pandas

import sqlite3
import requests
import google.generativeai as genai
import pandas as pd
import os
from google.colab import userdata #import colab userdata

# Step 1: Set up the Chinook database
url = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
with open("Chinook_Sqlite.sqlite", "wb") as f:
    f.write(requests.get(url).content)
conn = sqlite3.connect("Chinook_Sqlite.sqlite")
print("Database connected!")

# Step 2: Extract schema
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
schema = "Chinook Database Schema:\n"
for table in tables:
    table_name = table[0]
    schema += f"\nTable: {table_name}\n"
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        schema += f"  - {col[1]} ({col[2]})\n"

# Step 3: Define sample queries
sample_queries = """
Sample Queries:
1. "Show total sales by genre":
   SELECT g.Name AS Genre, SUM(il.UnitPrice * il.Quantity) AS TotalSales
   FROM InvoiceLine il
   JOIN Track t ON il.TrackId = t.TrackId
   JOIN Genre g ON t.GenreId = g.GenreId
   GROUP BY g.Name
   ORDER BY TotalSales DESC;

2. "List customers from USA":
   SELECT CustomerId, FirstName, LastName, Country
   FROM Customer
   WHERE Country = 'USA';

3. "Sales by year":
   SELECT STRFTIME('%Y', InvoiceDate) AS Year, SUM(Total) AS TotalSales
   FROM Invoice
   GROUP BY Year
   ORDER BY Year DESC;
"""

# Step 4: Configure Gemini API
#API_KEY = "your-gemini-api-key"  # Replace with your actual Gemini API key
api_key = "AIzaSyD5zcgB18WiKDtK2PwnzyJjbU9W9qhdiFg"
#userdata.get('GEMINI_API_KEY') #use userdata.get to retrieve the secret

if not api_key:
    print("Please set the GEMINI_API_KEY secret in Colab.")
    exit(1)
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")  # Adjust model name as per availability

# Prompt template for Gemini
prompt_template = f"""
{schema}

{sample_queries}

User Request: "{{user_input}}"
Generate an SQL query to fulfill the user's request based on the schema and sample queries above. Provide only the SQL query as output, enclosed in ```sql``` tags.
"""

# Step 5: Generate SQL with Gemini
def generate_sql(user_input):
    prompt = prompt_template.format(user_input=user_input)
    response = model.generate_content(prompt)
    sql_text = response.text.strip()
    
    # Extract SQL from ```sql``` tags
    if "```sql" in sql_text:
        sql_query = sql_text.split("```sql")[1].split("```")[0].strip()
        return sql_query
    return None

# Step 6: Fetch and format report
def get_report(user_input):
    sql_query = generate_sql(user_input)
    if not sql_query:
        return "Sorry, I couldn’t generate a valid SQL query for that request."
    
    try:
        df = pd.read_sql_query(sql_query, conn)
        return f"Report Generated:\n{df.to_string(index=False)}"
    except Exception as e:
        return f"Error executing query: {str(e)}\nGenerated SQL: {sql_query}"

# Step 7: Chatbot loop
def chat():
    print("Chatbot: Hi! Ask me for reports (e.g., 'sales by genre', 'customers in USA'). Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Chatbot: Goodbye!")
            break
        response = get_report(user_input)
        print(f"Chatbot: {response}")

# Start the chatbot
chat()
