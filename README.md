# 🤖 SQL Query AI Agent


An AI-driven system that converts natural language queries into SQL commands and executes them on a database, enhanced with Explainable AI (XAI) for transparency and trust.

---

## 🎯 Problem Statement
Traditional database interaction requires SQL knowledge, creating a barrier for non-technical users and increasing dependency on technical teams.

---

## 💡 Solution
Developed an intelligent NL2SQL system that allows users to interact with databases using natural language while providing explanations of AI decisions using LIME and SHAP.

---

## 🚀 Key Features
- 💬 Natural Language → SQL conversion  
- ⚡ Real-time query execution  
- 🔍 Explainable AI (LIME + SHAP integration)  
- 🧠 Schema-aware query generation  
- 🔒 SQL safety validation (blocks DROP/ALTER)  
- 📊 Supports CRUD, JOIN, Aggregations  
- 🌐 Interactive UI (Streamlit)  

---

## 🛠️ Tech Stack

**AI & Backend**
- Python  
- OpenAI GPT-3.5  
- LangChain  
- Flask  

**Database**
- MySQL  
- SQLAlchemy  

**Frontend**
- Streamlit  

**Explainable AI**
- LIME  
- SHAP  

**ML Models**
- Scikit-learn  
- XGBoost  

---

## 🏗️ System Architecture
User Query (Natural Language)
│
▼
LLM (GPT-3.5 via LangChain)
│
▼
SQL Generation + Validation
│
▼
MySQL Database
│
▼
Query Result
│
▼
Explainable AI Layer (LIME + SHAP)
│
▼
Final Output + Explanation


---

## ⚙️ How It Works
1. User enters a query in natural language  
2. LLM interprets intent & generates SQL  
3. SQL is validated (safety layer)  
4. Query executes on database  
5. Results are returned  
6. LIME & SHAP explain AI decision  

---

## 📊 Performance
- 🎯 Accuracy: **92%**  
- ⚡ Average Response Time: **~1.7 seconds**  
- 🔍 XAI Explanation Overhead: **~0.3 sec**  

---

## 🔐 Safety Features
- Blocks destructive queries (DROP, ALTER, DELETE ALL)  
- Prevents invalid SQL execution  

---

## 📈 Impact
- Enables non-technical users to access databases  
- Reduces dependency on SQL experts  
- Improves trust with explainable AI  
- Faster decision-making  

---

## 🔮 Future Improvements
- Voice-based queries  
- Multi-database support  
- Dashboard visualization  
- User authentication system  

---

## 📫 Connect With Me
- 📧 sumitchowdhuary4@gmail.com  
- 💼 https://www.linkedin.com/in/sumit-chowdhuary  

---

⭐ If you found this project useful, consider giving it a star!
