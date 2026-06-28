# 🤖 AI Chief of Staff (Workspace Orchestrator)

**AI Chief of Staff** is an advanced, multi-agent artificial intelligence system designed to automate and manage your workspace. Built using the **BeeAI Framework**, **LangChain**, and the **Model Context Protocol (MCP)**, this system acts as a highly intelligent executive assistant.

Instead of relying on a single AI to do everything, this project uses a "team" of specialized AI agents working together to read emails, draft replies, check your schedule, and book meetings—all using natural language.

---

## 🌟 Key Features

- **🧠 Intelligent Orchestration:** A central "Chief of Staff" AI understands your request, plans a multi-step workflow, and delegates tasks to the right specialist agents.
- **📧 Email Management (Gmail API):**
- Read and summarize unread emails.
- Perform advanced searches (e.g., "Find emails with attachments from my boss").
- Draft and dispatch professional email replies.

- **📅 Calendar Scheduling (Google Calendar API):**
- Check calendar availability and intelligently suggest alternative times if a slot is booked.
- Create, reschedule, or delete events.

- **⏳ Advanced Time Reasoning:** Understands human concepts of time like _"next Tuesday at 3 PM,"_ _"day before yesterday,"_ or _"end of next month."_
- **🔄 Agent-to-Agent (A2A) Communication:** Specialists talk to each other to handle complex requests (e.g., _"Find the email about the marketing sync and schedule a 30-min follow-up for tomorrow"_).

---

## 🏛️ How It Works (The Architecture)

This system uses an organizational hierarchy, much like a real corporate office:

1. **The Orchestrator (`orchestrator.py`):** The manager. You give it a command, it "thinks" about the best way to solve it, and hands off the work to its subordinates.
2. **The Specialists:**

- **Email Agent (`email_server.py` & `email_agent.py`):** The inbox specialist. It translates the Orchestrator's requests into specific Gmail actions.
- **Calendar Agent (`calender_agent_server.py` & `calender_agent.py`):** The scheduling specialist. It handles all Google Calendar math, timezones, and conflict resolutions.

3. **The MCP Engines (The "Hands"):** To ensure security and modularity, the agents do not touch your data directly. They send instructions to isolated **Model Context Protocol (MCP) servers** (`mcp_email_server.py`, `mcp_calender_server.py`), which actually execute the Python code to interact with Google's APIs.

---

## 🛠️ Setup & Installation

### 1. Prerequisites

- **Python 3.10+** installed on your machine.
- **Google Workspace Account** (for Gmail and Google Calendar).
- **API Keys:** \* Google Gemini API Key (for the LLM).
- Google Cloud Platform (GCP) OAuth Credentials (`credentials.json`) with Gmail and Calendar API scopes enabled.

### 2. Install Dependencies

Clone the repository and install the required Python packages (it is recommended to use a virtual environment):

```bash
pip install -r requirements.txt

```

_(Ensure you have libraries like `langchain`, `google-auth`, `google-api-python-client`, `beeai-framework`, `python-dotenv`, and `uvicorn` installed)._

### 3. Environment Variables (`.env`)

Create a `.env` file in the root directory of your project and populate it with the following:

```env
# AI Models
GOOGLE_API_KEY="your_gemini_api_key_here"
GEMINI_API_KEY="your_gemini_api_key_here"

# Google Workspace
GOOGLE_CALENDAR_ID="your_email@gmail.com"
CREDENTIALS_PATH="credentials.json"  # Path to your downloaded GCP OAuth file
TOKEN_PATH="token_gmail.json"        # Will be auto-generated upon first login
USERS_TIMEZONES_PATH="timezones.pkl" # For calendar timezone logic

# Ports & Hosting
AGENT_HOST="127.0.0.1"
ORCHESTRATOR_PORT=8000
EMAIL_AGENT_PORT=9001
SCHEDULER_AGENT_PORT=9002

```

### 4. Authentication

The first time you run the Email or Calendar agents, a browser window will open asking you to log in to your Google Account. This grants the local application permission to modify your emails and calendar. A `token.json` file will be saved locally so you don't have to log in every time.

---

## 🚀 Running the System

Because this is a multi-agent system, you need to spin up the independent servers so they can communicate with one another over your local network.

**Step 1: Start the Email Specialist**
Open a terminal and run:

```bash
python email_server.py

```

_(This starts the Email A2A server on port 9001, which internally spins up the MCP Gmail & Date engines)._

**Step 2: Start the Calendar Specialist**
Open a second terminal and run:

```bash
python calender_agent_server.py

```

_(This starts the Calendar A2A server on port 9002, which internally spins up the MCP Calendar engine)._

**Step 3: Start the Orchestrator**
Open a third terminal and run:

```bash
python orchestrator.py

```

_(This starts the main brain on port 8000, connecting to the specialists)._

---

## 💬 Usage Examples

Once the system is running, the Orchestrator is ready to accept queries. Here are examples of what you can ask your AI Chief of Staff:

**Simple Requests:**

- _"Do I have any unread emails from John?"_
- _"What does my calendar look like for tomorrow morning?"_
- _"Cancel my 3 PM meeting on Friday."_

**Complex / Multi-Agent Requests:**

- _"Check my emails for the latest invoice from AWS. Once you find it, schedule a 30-minute meeting with the accounting team for next Wednesday to discuss it."_
- _"Are there any urgent emails? If so, draft a reply saying I'll review them by tomorrow, and block out 1 hour on my calendar tomorrow morning to handle them."_

---

## 📁 File Structure Guide

- `orchestrator.py` - The main entry point and "brain" of the system.
- `email_agent.py` / `email_server.py` - The LLM logic and web server for the Email Specialist.
- `calender_agent.py` / `calender_agent_server.py` - The LLM logic and web server for the Calendar Specialist.
- `mcp_*.py` files - The isolated Model Context Protocol scripts that safely execute API calls and pass the raw data back to the AI.
- `calendar_logic.py` - Contains robust natural language date-parsing and timezone logic.
- `gmail_auth.py` - Handles Google OAuth2 security tokens.
