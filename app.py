import streamlit as st
import sqlite3
import ollama
import re

promptcol = [
    'Convert into a SQL query. Respond with only the SQL code and no explanation.',
    'Convert into Insert Query. Respond with only the SQL code and no explanation.',
    'Convert the given into SQL query with only SQL code and no explanation at all'
]

conn = sqlite3.connect("User.db")
cur = conn.cursor()
conn.close()

def executeUser(response):
    try:
        cur.execute(response)
        conn.commit()
        if response.strip().lower().startswith("select"):
            rows = cur.fetchall()
            st.dataframe(rows)
            conn.close()
        else:
            st.success("Query Executed Successfully")
    except Exception as e:
        st.error(f'Error: {e}')

def readNLPQ(input):
    response = ollama.chat(
        model='mistral',
        messages=[
            {'role': 'system', 'content': promptcol[2]},
            {'role': 'user', 'content': input}
        ]
    )
    return response['message']['content']

def insertRow(query):
    try:
        conn.execute(query)
        conn.commit()
        st.success("✅ Row inserted successfully!")
    except Exception as e:
        st.error(f'❌ Error inserting row: {e}')
        st.code(query, language='sql')

def rowclean(query):
    query = re.sub(r"```sql|```|'''|\"\"\"", '', query, flags=re.IGNORECASE).strip()
    query = re.split(r';\s*', query)[0] + ';'
    return query.strip()

def clean(query):
    query = re.sub(r"```sql|```|'''|\"\"\"", '', query, flags=re.IGNORECASE).strip()
    query = re.split(r';\s*', query)[0] + ';'
    return query.strip()

def readNlprow(row, table, columns):
    user_prompt = f"Insert row in `{table}` with the following columns: {columns} and inserting value {row}"
    response = ollama.chat(
        model='mistral',
        messages=[
            {"role": "system", "content": promptcol[1]},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response['message']['content']

def readNlp(columns, table):
    s_table = f'"{table}"'
    user_prompt = f"Create a SQL query to create a table named `{s_table}` with the following columns: {columns}"
    response = ollama.chat(
        model='mistral',
        messages=[
            {"role": "system", "content": promptcol[0]},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response['message']['content']

def tableCreation(query):
    try:
        cur.execute(query)
        conn.commit()
        st.success("✅ Table created successfully!")
    except Exception as e:
        st.error(f"❌ Error creating table: {e}")
        st.code(query, language='sql')

def frontend():
    st.set_page_config(page_title="SQL Table Creator", page_icon="📋", layout="centered")
    st.title("🧠 AI SQL Table Generator")

    st.markdown("### 1️⃣ Generate & Create Table")
    table = st.text_input("Enter Table Name (avoid SQL keywords like `order`):")
    columns = st.text_area("Enter Columns (e.g., `id INTEGER PRIMARY KEY, name TEXT, price REAL`)")

    if st.button("🚀 Generate SQL & Create Table"):
        if table.strip() and columns.strip():
            response = readNlp(columns.strip(), table.strip())
            cleaned_query = clean(response)
            st.code(cleaned_query, language='sql')
            tableCreation(cleaned_query)
        else:
            st.warning("⚠️ Please provide both table name and column definitions.")

    st.markdown("---")
    st.markdown("### 2️⃣ Insert Row into Table")
    row = st.text_area("Insert Row (e.g., `1, 'Apple', 9.99`):")

    if st.button("Insert Row"):
        if row.strip() and table.strip() and columns.strip():
            raw_response = readNlprow(row, table.strip(), columns.strip())
            cleaned = rowclean(raw_response)
            st.code(cleaned, language='sql')
            insertRow(cleaned)
        else:
            st.warning("⚠️ Please ensure table, columns, and row are all provided.")

    if st.button("Show Table"):
        try:
            data = cur.execute(f'SELECT * FROM {table}').fetchall()
            st.dataframe(data)
        except Exception as e:
            st.error(f"Fetch error: {e}")

    st.markdown("### 3️⃣ Ask in Natural Language (AI-Powered)")
    user_input = st.text_area("Ask a question about your data:")

    if st.button("Generate and Run Query"):
        query = clean(readNLPQ(user_input))
        st.code(query, language='sql')
        executeUser(query)

frontend()
