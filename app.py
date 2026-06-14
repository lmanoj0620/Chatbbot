import streamlit as st
import requests
import json
import re
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SQL Query Generator",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .hero-title {
    font-size: 2.4rem; font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    text-align: center; margin-bottom: .3rem;
  }
  .hero-sub {
    text-align: center; color: #6b7280; font-size: .95rem; margin-bottom: 1.5rem;
  }

  /* Chat bubbles */
  .msg-user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white; border-radius: 18px 18px 4px 18px;
    padding: 12px 18px; margin: 8px 0 8px 15%;
    box-shadow: 0 2px 8px rgba(102,126,234,.35);
  }
  .msg-bot {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 18px 18px 18px 4px;
    padding: 14px 18px; margin: 8px 15% 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
  }
  .msg-label {
    font-size: .72rem; font-weight: 600; letter-spacing: .05em;
    text-transform: uppercase; opacity: .7; margin-bottom: 4px;
  }

  /* SQL block */
  .sql-block {
    background: #0f172a; color: #e2e8f0;
    border-radius: 10px; padding: 16px;
    font-family: 'Courier New', monospace; font-size: .85rem;
    line-height: 1.6; overflow-x: auto;
    border-left: 4px solid #667eea;
    white-space: pre-wrap; word-break: break-word;
  }
  .sql-keyword { color: #93c5fd; font-weight: bold; }
  .sql-func    { color: #86efac; }
  .sql-string  { color: #fde68a; }
  .sql-comment { color: #6b7280; font-style: italic; }

  /* Badges */
  .badge {
    display: inline-block; padding: 2px 10px;
    border-radius: 12px; font-size: .72rem; font-weight: 600;
    margin: 0 3px 4px 0;
  }
  .badge-blue   { background: #dbeafe; color: #1d4ed8; }
  .badge-green  { background: #dcfce7; color: #15803d; }
  .badge-purple { background: #f3e8ff; color: #7e22ce; }

  /* Sidebar */
  section[data-testid="stSidebar"] { background: #f8fafc; }

  /* Chat container scroll */
  .chat-container { max-height: 65vh; overflow-y: auto; padding-right: 6px; }

  /* Empty state */
  .empty-state {
    text-align: center; padding: 3rem 1rem; color: #94a3b8;
  }
  .empty-icon { font-size: 3.5rem; margin-bottom: .5rem; }

  /* Toast-style notice */
  .notice {
    background: #fffbeb; border: 1px solid #fcd34d;
    border-radius: 8px; padding: 10px 14px;
    font-size: .85rem; color: #92400e; margin-bottom: 1rem;
  }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
HF_API_BASE = "https://api-inference.huggingface.co/models/"

MODELS = {
    "SQLCoder-7B  (Best SQL accuracy)": "defog/sqlcoder-7b-2",
    "Mistral-7B Instruct  (Balanced)": "mistralai/Mistral-7B-Instruct-v0.2",
    "Zephyr-7B Beta  (Fast & good)": "HuggingFaceH4/zephyr-7b-beta",
    "Flan-T5-Large  (Lightweight)": "google/flan-t5-large",
}

EXAMPLE_QUESTIONS = [
    "Find the top 5 customers by total purchase amount",
    "Show all orders placed in the last 30 days with customer names",
    "Get the average salary per department, sorted highest first",
    "List products that are out of stock",
    "Find duplicate email addresses in the users table",
    "Calculate monthly revenue for the current year",
    "Show employees who have not placed any orders",
    "Get the second highest salary from employees table",
]

SAMPLE_SCHEMAS = {
    "E-Commerce": """
-- Customers
CREATE TABLE customers (
    id         INT PRIMARY KEY,
    name       VARCHAR(100),
    email      VARCHAR(100) UNIQUE,
    created_at TIMESTAMP
);

-- Products
CREATE TABLE products (
    id         INT PRIMARY KEY,
    name       VARCHAR(200),
    price      DECIMAL(10,2),
    stock      INT,
    category   VARCHAR(50)
);

-- Orders
CREATE TABLE orders (
    id          INT PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    total       DECIMAL(10,2),
    status      VARCHAR(20),
    created_at  TIMESTAMP
);

-- Order Items
CREATE TABLE order_items (
    id         INT PRIMARY KEY,
    order_id   INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity   INT,
    unit_price DECIMAL(10,2)
);
""",
    "HR Database": """
CREATE TABLE departments (
    id   INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE employees (
    id            INT PRIMARY KEY,
    name          VARCHAR(100),
    email         VARCHAR(100),
    salary        DECIMAL(10,2),
    department_id INT REFERENCES departments(id),
    manager_id    INT REFERENCES employees(id),
    hire_date     DATE
);
""",
    "Blog Platform": """
CREATE TABLE users (
    id         INT PRIMARY KEY,
    username   VARCHAR(50) UNIQUE,
    email      VARCHAR(100),
    role       VARCHAR(20)  -- 'admin', 'author', 'reader'
);

CREATE TABLE posts (
    id           INT PRIMARY KEY,
    title        VARCHAR(200),
    content      TEXT,
    author_id    INT REFERENCES users(id),
    published_at TIMESTAMP,
    status       VARCHAR(20)  -- 'draft', 'published', 'archived'
);

CREATE TABLE comments (
    id         INT PRIMARY KEY,
    post_id    INT REFERENCES posts(id),
    user_id    INT REFERENCES users(id),
    body       TEXT,
    created_at TIMESTAMP
);

CREATE TABLE tags (
    id   INT PRIMARY KEY,
    name VARCHAR(50)
);

CREATE TABLE post_tags (
    post_id INT REFERENCES posts(id),
    tag_id  INT REFERENCES tags(id)
);
""",
    "Custom (paste yours)": "",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def highlight_sql(sql: str) -> str:
    keywords = (
        "SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|FULL|CROSS|ON|AS|"
        "GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|UNION|ALL|DISTINCT|"
        "INSERT INTO|UPDATE|DELETE|SET|VALUES|CREATE|ALTER|DROP|TABLE|"
        "INDEX|VIEW|WITH|CASE|WHEN|THEN|ELSE|END|AND|OR|NOT|IN|EXISTS|"
        "BETWEEN|LIKE|IS|NULL|ASC|DESC|COUNT|SUM|AVG|MAX|MIN|COALESCE|"
        "CAST|CONVERT|DATE|TIMESTAMP|NOW|YEAR|MONTH|DAY|SUBQUERY|CTE"
    )
    sql_escaped = sql.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # comments
    sql_escaped = re.sub(
        r"(--[^\n]*)", r'<span class="sql-comment">\1</span>', sql_escaped
    )
    # strings
    sql_escaped = re.sub(
        r"('(?:[^'\\]|\\.)*')",
        r'<span class="sql-string">\1</span>',
        sql_escaped,
    )
    # keywords
    sql_escaped = re.sub(
        rf"\b({keywords})\b",
        r'<span class="sql-keyword">\1</span>',
        sql_escaped,
        flags=re.IGNORECASE,
    )
    return f'<div class="sql-block">{sql_escaped}</div>'


def build_prompt(requirement: str, schema: str, dialect: str) -> str:
    schema_section = f"\n### Database Schema:\n```sql\n{schema.strip()}\n```\n" if schema.strip() else ""
    return f"""You are an expert SQL developer. Generate a clean, optimized {dialect} SQL query for the given requirement.

{schema_section}
### Requirement:
{requirement}

### Rules:
- Return ONLY the SQL query (no markdown fences, no explanation before the query)
- After the query, add a brief 1-2 line explanation starting with --EXPLANATION:
- Use proper indentation and formatting
- Use table aliases for readability when joining multiple tables
- Add comments inside the query for complex logic

### SQL Query:
"""


def call_hf_api(prompt: str, model_id: str, api_token: str) -> tuple[str, str]:
    """Returns (sql, explanation) or raises an exception."""
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 600,
            "temperature": 0.05,
            "top_p": 0.9,
            "do_sample": True,
            "return_full_text": False,
        },
    }

    resp = requests.post(f"{HF_API_BASE}{model_id}", headers=headers, json=payload, timeout=60)

    if resp.status_code == 503:
        raise RuntimeError("Model is loading — please wait 20 s and retry.")
    if resp.status_code == 401:
        raise RuntimeError("Invalid HuggingFace API token.")
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    raw = ""
    if isinstance(data, list) and data:
        raw = data[0].get("generated_text", "")
    elif isinstance(data, dict):
        raw = data.get("generated_text", "")

    # Split SQL from explanation
    explanation = ""
    if "--EXPLANATION:" in raw:
        parts = raw.split("--EXPLANATION:", 1)
        sql = parts[0].strip()
        explanation = parts[1].strip()
    else:
        sql = raw.strip()

    # Strip any accidental markdown fences
    sql = re.sub(r"^```(?:sql)?", "", sql, flags=re.IGNORECASE).strip()
    sql = re.sub(r"```$", "", sql).strip()

    return sql, explanation


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    api_token = st.text_input(
        "HuggingFace API Token",
        type="password",
        placeholder="hf_xxxxxxxxxxxxxxxxxxxx",
        help="Get a free token at huggingface.co/settings/tokens",
    )

    model_label = st.selectbox("Model", list(MODELS.keys()))
    model_id = MODELS[model_label]

    dialect = st.selectbox(
        "SQL Dialect",
        ["Standard SQL", "PostgreSQL", "MySQL", "SQLite", "SQL Server", "BigQuery"],
    )

    st.markdown("---")
    st.markdown("### 🗂️ Database Schema")
    schema_preset = st.selectbox("Load sample schema", list(SAMPLE_SCHEMAS.keys()))
    preset_value = SAMPLE_SCHEMAS[schema_preset]

    schema_input = st.text_area(
        "Paste your CREATE TABLE statements",
        value=preset_value,
        height=260,
        placeholder="CREATE TABLE orders (\n  id INT,\n  ...\n);",
    )

    st.markdown("---")
    st.markdown("### 💡 Quick Examples")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, key=f"ex_{q[:20]}", use_container_width=True):
            st.session_state["prefill"] = q

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.query_count = 0
        st.rerun()

    st.markdown(
        f"<div style='text-align:center;color:#94a3b8;font-size:.8rem;'>"
        f"Queries generated: <b>{st.session_state.query_count}</b></div>",
        unsafe_allow_html=True,
    )

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">🗄️ SQL Query Generator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Describe what data you need → get production-ready SQL instantly</div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
col1.metric("Model", model_label.split("(")[0].strip())
col2.metric("Dialect", dialect)
col3.metric("Schema", schema_preset if schema_input.strip() else "None")

st.divider()

# ── Chat area ──────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-state">
          <div class="empty-icon">💬</div>
          <b>Start a conversation</b><br>
          Describe the data you need in plain English and I'll write the SQL for you.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-user">'
                f'<div class="msg-label">You</div>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            sql = msg.get("sql", "")
            explanation = msg.get("explanation", "")
            highlighted = highlight_sql(sql)
            exp_html = (
                f'<div style="margin-top:10px;font-size:.85rem;color:#4b5563;">'
                f'<b>💡 Explanation:</b> {explanation}</div>'
                if explanation
                else ""
            )
            badges = (
                f'<div style="margin-bottom:8px;">'
                f'<span class="badge badge-blue">{dialect}</span>'
                f'<span class="badge badge-purple">{model_label.split("(")[0].strip()}</span>'
                f'<span class="badge badge-green">{msg.get("ts","")}</span>'
                f'</div>'
            )
            st.markdown(
                f'<div class="msg-bot">'
                f'<div class="msg-label">Assistant</div>'
                f'{badges}'
                f'{highlighted}'
                f'{exp_html}'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Copy-friendly expander
            with st.expander("📋 Copy raw SQL"):
                st.code(sql, language="sql")

# ── Input area ─────────────────────────────────────────────────────────────────
st.markdown("---")

prefill = st.session_state.pop("prefill", "")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Your requirement",
        value=prefill,
        placeholder="e.g. Find the top 10 customers by total spend in the last 90 days",
        height=90,
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("⚡ Generate SQL", use_container_width=True, type="primary")

# ── Generation logic ───────────────────────────────────────────────────────────
if submitted:
    if not api_token:
        st.markdown(
            '<div class="notice">⚠️ Please enter your HuggingFace API token in the sidebar. '
            'Get one free at <a href="https://huggingface.co/settings/tokens" target="_blank">'
            'huggingface.co/settings/tokens</a></div>',
            unsafe_allow_html=True,
        )
    elif not user_input.strip():
        st.warning("Please describe what you need.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})

        with st.spinner(f"Generating SQL with {model_label.split('(')[0].strip()}…"):
            try:
                prompt = build_prompt(user_input.strip(), schema_input, dialect)
                sql, explanation = call_hf_api(prompt, model_id, api_token)

                ts = datetime.now().strftime("%H:%M")
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "sql": sql,
                        "explanation": explanation,
                        "ts": ts,
                    }
                )
                st.session_state.query_count += 1
                st.rerun()

            except RuntimeError as e:
                st.error(str(e))
            except requests.exceptions.Timeout:
                st.error("Request timed out. The model may be under heavy load — try again.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#cbd5e1;font-size:.78rem;margin-top:2rem;'>"
    "Powered by HuggingFace Inference API · Built with Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
