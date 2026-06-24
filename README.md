# 🤖 AstraFlow — Full-Stack Multi-Agent Workspace 📅⚡

> An offline-first **full-stack multi-agent planner and scheduling platform** built using **ADK-inspired workflow principles** and **MCP-style tool architecture**.

---

# 🌐 Live Demo

🚀 **Runs Completely Offline**

> No API keys. No cloud dependency. No external AI services.

⚠️ The entire system executes locally on your machine.

---

# 🚀 Overview

**AstraFlow** is a developer-focused intelligent planning platform that orchestrates multiple agents to create optimized study, work, and life schedules.

The platform leverages workflow graph concepts, local tool servers, and secure CLI skills to coordinate autonomous components capable of prioritizing, organizing, and scheduling tasks.

<img width="1536" height="1024" alt="Image" src="https://github.com/user-attachments/assets/82ecc4ac-4029-44b0-822d-a7e7ba16bcb5" />
<img width="1918" height="1012" alt="Image" src="https://github.com/user-attachments/assets/e4477e75-12ec-4f94-8f10-7917c129527b" />
<img width="1906" height="1012" alt="Image" src="https://github.com/user-attachments/assets/9937cb62-5fda-465e-9dfd-c34edadd4959" />
### 🧠 AstraFlow allows users to:

* 🤖 Coordinate multiple specialized agents
* 📅 Generate conflict-free schedules automatically
* 📚 Build active recall study plans
* ⚡ Prioritize tasks using the Eisenhower Matrix
* 🔄 Export schedules directly to calendar applications
* 🔒 Run everything fully offline with enhanced security

Built with a modern dashboard interface, AstraFlow delivers an AI-powered productivity experience without relying on external APIs.

---

# ✨ Key Features

## 🤖 Multi-Agent Workflow

* 🧠 **Planner Agent** → Parses user requests and orchestrates workflow execution
* ⚡ **Task Optimization Agent** → Prioritizes tasks based on urgency and importance
* 📚 **Study Planning Agent** → Generates active recall cards and study sessions
* 📅 **Life Scheduler Agent** → Creates optimized schedules and resolves conflicts
* 🔄 Sequential workflow execution pipeline

```text
START → Planner → Optimizer → Study → Scheduler → END
```

---

## 🔌 Tool Server Architecture

The platform exposes local tools through a structured tool-calling architecture.

### Available Tools

* 🛠️ `optimize_priority`
* 📚 `generate_study_cards`
* 📅 `schedule_event`

### Features

* 📦 Structured JSON communication
* ⚡ Local tool invocation
* 🔒 Fully offline execution
* 🧩 Standardized tool schemas

---

## 📅 Intelligent Scheduling Engine

* 🕒 Automatic time-slot generation
* ⚠️ Conflict detection and resolution
* 📆 Weekly calendar planning
* 🧠 Study and productivity balancing
* 🎯 Goal-driven schedule optimization

---

## 📤 CLI Skills & Export System

The secure CLI tool (`astraflow-cli`) allows:

* 📅 Export schedules as `.ics` calendar files
* 📝 Generate Markdown topic summaries
* ⚡ Trigger backend workflow skills safely

---

# 🔒 Security Architecture

Security is a first-class citizen in AstraFlow.

### 🛡️ Implemented Security Measures

### 🚫 Path Traversal Protection

* Prevents unauthorized file access outside workspace
* Blocks parent directory references (`../`)

### 🔐 Subprocess Sanitization

* Sanitizes user inputs before shell execution

### 📏 Input Boundary Validation

* Limits prompts to safe lengths
* Removes unsafe HTML-like tags

### ⏱️ Subprocess Isolation

* Executes CLI skills using secure subprocesses with strict timeout policies

### 🏠 Workspace Restriction

* All generated files remain inside the local project workspace

---

# 🏗️ System Architecture

```mermaid
graph TD

    User([👤 User Prompt]) --> Planner[🧠 Planner Agent]

    Planner --> TaskOpt[⚡ Task Optimization Agent]
    TaskOpt --> StudyAgent[📚 Study Planning Agent]
    StudyAgent --> Scheduler[📅 Life Scheduler Agent]

    TaskOpt -.-> Tool1[optimize_priority]
    StudyAgent -.-> Tool2[generate_study_cards]
    Scheduler -.-> Tool3[schedule_event]

    Tool3 --> DB[(calendar_db.json)]

    Scheduler --> Dashboard[📊 Dashboard]
    Scheduler --> Export[📅 weekly_schedule.ics]
```

---

# 🛠️ Tech Stack

| Layer         | Technology                |
| ------------- | ------------------------- |
| Frontend      | HTML5, CSS3, JavaScript   |
| Backend       | Python, FastAPI           |
| Architecture  | Multi-Agent Workflow      |
| Communication | JSON-based Tool Calling   |
| Data Storage  | JSON Database             |
| CLI Skills    | Python Subprocess         |
| Deployment    | Local Offline Environment |

---

# 📂 Project Structure

```text
AstraFlow/
│
├── agents.py                  # 🤖 Multi-Agent Workflow
├── server.py                  # 🚀 FastAPI Backend
├── mcp_server.py              # 🔌 MCP Tool Server
├── cli_tool.py                # ⚡ CLI Skills
├── calendar_db.json           # 📅 Local Calendar Storage
├── requirements.txt           # 📦 Dependencies
├── static/                    # 🌐 Frontend Assets
├── templates/                 # 🖥️ Dashboard UI
├── README.md
│
└── generated/
    ├── weekly_schedule.ics    # 📤 Calendar Export
    └── study_notes.md         # 📝 Generated Notes
```

---

# ⚙️ Installation

## 📌 Requirements

Before running this project, ensure you have:

✅ Python 3.13+

✅ pip

---

## 📥 Setup

Clone the repository:

```bash
git clone https://github.com/shivam-786-sys/AstraFlow.git

cd AstraFlow
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Project

Start the application:

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 3000
```

Open in browser:

```text
http://localhost:3000
```

---

# 🎬 End-to-End Demo Flow

## 1️⃣ Enter User Request

Example:

> "I have a chemistry exam next Friday. Schedule study sessions and gym slots."

---

## 2️⃣ Workflow Execution

* 🧠 Planner Agent parses request
* ⚡ Optimizer Agent prioritizes tasks
* 📚 Study Agent generates learning materials
* 📅 Scheduler Agent resolves conflicts
* 💾 Events stored locally

---

## 3️⃣ Review Results

* 💬 View workflow results
* 📊 Inspect generated schedules
* 📅 Analyze calendar timelines

---

## 4️⃣ Export Schedule

Generate:

```text
weekly_schedule.ics
```

Import directly into:

* Google Calendar
* Outlook Calendar
* Apple Calendar

---

# 🔒 Offline First

✅ No OpenAI API

✅ No Gemini API

✅ No External Services

✅ No Internet Required

Everything runs entirely on your local machine.

---

# 🚀 Future Improvements

* 🌐 Cloud synchronization
* 🧠 Local LLM integration
* 🔔 Smart notifications
* 📱 Mobile companion app
* 🎙️ Voice-enabled planning assistant

---

# 👨‍💻 Author

**Shivam Dwivedi**

Built with ❤️ for **AI Engineering, Full-Stack Development, and Multi-Agent Systems**

GitHub: https://github.com/shivam-786-sys

---

# 📜 License

This project is licensed under the **MIT License**.

---

# ⚡ Final Tagline

> **Plan Smarter. Learn Faster. Organize Everything.**
