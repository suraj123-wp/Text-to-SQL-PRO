from dotenv import load_dotenv
import os
import google.generativeai as genai
import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import pooling

# ✅ Load environment variables
load_dotenv()

# ✅ Configure Gemini with your API key from environment variables
api_key = os.getenv("Google_API_KEY")
if not api_key:
    st.error("Google API Key not found in environment variables!")
else:
    genai.configure(api_key=api_key)

# ✅ Correct model name (avoid NotFound error)
MODEL_NAME = "models/gemini-2.0-flash-lite"  # Change to "gemini-1.5-pro" if you're using the v1.5 version and have access

prompt = """
You are a SQL expert. Convert the user's natural language request into a valid SQL query.
Assume the database is MySQL and there is a table called 'sales_data' with the following columns:
sale_date, Channel, Product_Name, City, Quantity, Sales.
Only return the SQL query. Do not include explanations or extra text.

Examples:
1. "Show total sales and quantity per city" means:
   SELECT City, SUM(Sales) AS Total_Sales, SUM(Quantity) AS Total_Quantity FROM sales_data GROUP BY City
2. "Which city had the highest sales in 2024" means:
   SELECT City, SUM(Sales) AS Total_Sales FROM sales_data WHERE sale_date BETWEEN '2024-01-01' AND '2024-12-31' GROUP BY City ORDER BY Total_Sales DESC LIMIT 1
...
"""

# ✅ Function to get SQL query from Gemini
def get_gemini_response(question, prompt):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content([prompt, question])
        sql_query = response.text.strip()
        # Clean up the query further if needed
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        return sql_query
    except Exception as e:
        st.error(f"Error generating SQL: {str(e)}")
        return None

# ✅ Optimized MySQL Connection Pooling
db_config = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "Sonali1@2",
    "database": "sales_data_db"
}

# Connection pool initialization
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="sales_data_pool",
    pool_size=10,  # Adjust the pool size based on the number of concurrent requests
    **db_config
)

# ✅ Function to execute SQL query using connection pooling
def execute_sql_query(sql):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]
        conn.close()  # Return the connection to the pool
        return rows, col_names
    except mysql.connector.Error as e:
        st.error(f"MySQL Error: {str(e)}")
        return [], []
    except Exception as e:
        st.error(f"General Error: {str(e)}")
        return [], []

# ✅ Streamlit UI
st.set_page_config(page_title="SQL Assistant")
st.header("🤖 Gemini SQL Query Generator")

# Text input for question
question = st.text_input("🔍 Ask your data question (in plain English):", key="input")

# Button to generate SQL query and run it
submit = st.button("Get SQL & Run")

# ✅ Optimized logic for running SQL and fetching results
if submit and question:
    with st.spinner("Generating SQL and fetching data..."):
        sql_query = get_gemini_response(question, prompt)
        
        if sql_query:
            st.subheader("🧠 Generated SQL Query:")
            st.code(sql_query, language="sql")

            # Execute SQL query
            data, columns = execute_sql_query(sql_query)

            st.subheader("📊 Query Results:")
            if data:
                df = pd.DataFrame(data, columns=columns)
                st.dataframe(df)
            else:
                st.warning("No data returned.")
        else:
            st.error("Failed to generate SQL query.")
