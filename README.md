


# Mini SQL Agent – Natural Language Database Interface (v1)

## 📌 Overview

This project implements a **natural-language to SQL agent** that allows users to query and modify multiple mock databases using plain English.
It supports **CRUD operations** with a **human-in-the-loop verification system** to ensure safe database modifications.

The project is built with:

* **Python + FastAPI** for backend REST API
* **SQLite** for multiple mock databases (HR, Healthcare, E-commerce, Finance, Education)
* **Gemini API** for natural language → SQL parsing
* **Docker** for containerized deployment in future.

---

## 🚀 Features

* 🔹 **Interact with 5 mock databases** (`hr.db`, `healthcare.db`, `ecommerce.db`, `finance.db`, `education.db`)
* 🔹 **Natural language CRUD support** (Read/Write/Update/Delete)
* 🔹 **Human-in-the-loop approval** for Create/Update/Delete before commit
* 🔹 **Pending queue manager** to track and approve/reject modifications
* 🔹 **FastAPI REST endpoints** with interactive Swagger UI


---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/mini-sql-agent.git
cd mini-sql-agent
```

### 2. Create Virtual Environment (Optional)

```bash
python -m venv venv
source venv/bin/activate   # on Linux/Mac
venv\Scripts\activate      # on Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here

```



### 5. Run FastAPI App

with Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

---

## 🖥️ API Usage

Once running, access:

* API Docs: [http://localhost:8000/docs](http://localhost:8000/docs) and initialize database and test your nl-queries
* Example endpoint: `/query?text=Show all employees in HR&db=hr`

---

## 🐳 Docker Deployment in future

### Build Image

```bash
docker build -t mini-sql-agent:v1 .
```

### Run Container

```bash
docker run -d -p 8000:8000 --env-file .env mini-sql-agent:v1
```

---

## 📂 Project Structure

```
.
├── data/                 # SQLite databases
├── init_db.py            # Initialize mock databases
├── llm_parser.py         # Natural language → SQL parser (Gemini)
├── pending_manager.py    # Human-in-the-loop CRUD approval manager
├── main.py               # FastAPI entrypoint
├── requirements.txt
└── README.md
```

---

## ✅ Status

This is **Version 1** of the project:

* Implements all core requirements (multi-DB, CRUD, human-in-loop, FastAPI, Docker).
* **Does not yet use LangChain/LangGraph** – these will be integrated in a future version.

---
=======


# Mini SQL Agent – Natural Language Database Interface (v1)

## 📌 Overview

This project implements a **natural-language to SQL agent** that allows users to query and modify multiple mock databases using plain English.
It supports **CRUD operations** with a **human-in-the-loop verification system** to ensure safe database modifications.

The project is built with:

* **Python + FastAPI** for backend REST API
* **SQLite** for multiple mock databases (HR, Healthcare, E-commerce, Finance, Education)
* **Gemini API** for natural language → SQL parsing
* **Docker** for containerized deployment in future.

---

## 🚀 Features

* 🔹 **Interact with 5 mock databases** (`hr.db`, `healthcare.db`, `ecommerce.db`, `finance.db`, `education.db`)
* 🔹 **Natural language CRUD support** (Read/Write/Update/Delete)
* 🔹 **Human-in-the-loop approval** for Create/Update/Delete before commit
* 🔹 **Pending queue manager** to track and approve/reject modifications
* 🔹 **FastAPI REST endpoints** with interactive Swagger UI


---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/mini-sql-agent.git
cd mini-sql-agent
```

### 2. Create Virtual Environment (Optional)

```bash
python -m venv venv
source venv/bin/activate   # on Linux/Mac
venv\Scripts\activate      # on Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here

```



### 5. Run FastAPI App

with Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

---

## 🖥️ API Usage

Once running, access:

* API Docs: [http://localhost:8000/docs](http://localhost:8000/docs) and initialize database and test your nl-queries
* Example endpoint: `/query?text=Show all employees in HR&db=hr`

---

## 🐳 Docker Deployment in future

### Build Image

```bash
docker build -t mini-sql-agent:v1 .
```

### Run Container

```bash
docker run -d -p 8000:8000 --env-file .env mini-sql-agent:v1
```

---

## 📂 Project Structure

```
.
├── data/                 # SQLite databases
├── init_db.py            # Initialize mock databases
├── llm_parser.py         # Natural language → SQL parser (Gemini)
├── pending_manager.py    # Human-in-the-loop CRUD approval manager
├── main.py               # FastAPI entrypoint
├── requirements.txt
└── README.md
```

---

## ✅ Status

This is **Version 1** of the project:

* Implements all core requirements (multi-DB, CRUD, human-in-loop, FastAPI, Docker).
* **Does not yet use LangChain/LangGraph** – these will be integrated in a future version.

---
>>>>>>> 3b789c9adac507876f70584ab96d11ca45622e72
