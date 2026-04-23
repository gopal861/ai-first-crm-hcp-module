# AI-First CRM HCP Module - Log Interaction Screen

## Overview
Traditional Customer Relationship Management systems for Healthcare Professionals require field representatives to manually navigate forms and enter data. This manual data entry is slow and distracts representatives from their core interactions. 

This system is an AI-first CRM module designed to eliminate manual data entry. It provides a conversational interface where representatives can log interaction details using natural language or structured forms. Under the hood, an AI agent parses the input to extract structured data, handles incremental updates, and persists the data to a database.

## Key Features
- Natural language to structured data extraction
- Multi-step stateful conversation capability
- Incremental updates for individual fields without overwriting previous data
- Validation checks for required constraints before submission
- Integrated database persistence

## Architecture / System Design
The application follows a client-server architecture paired with an agentic state machine for processing.

1. **Client Layer**: A React frontend captures user input via a chat interface and maintains a live, read-only representation of the parsed form state using Redux.
2. **API Layer**: A FastAPI server exposes the application logic and acts as a gateway for the frontend.
3. **Agent Layer**: The system uses LangGraph to manage interactions. The agent acts as a router, combining deterministic heuristics and LLM classification to decide which operational tool to engage.
4. **Data Mutators**: Based on the intent, specific node functions mutate a shared state object in memory or run extraction procedures using the LLM.
5. **Persistence Layer**: Once the interaction is fully parsed and validated, the final structured payload is mapped through an SQLAlchemy ORM and written to a PostgreSQL database.

## LangGraph Agent & Tool Definitions
LangGraph orchestrates the state machine. Its primary role is interpreting the user's intent from unstructured text and passing execution control to the correct tool while retaining context across multiple conversation turns.

The agent utilizes the following specific tools:
1. **Log Interaction**: Extracts entities (HCP name, dates, topics discussed) from natural language using a combination of strictly typed LLM JSON outputs and regex patterns. It safely appends this data to the active state.
2. **Edit Interaction**: Identifies specific fields the user wants to correct (e.g., changing the sentiment from positive to neutral) and applies delta updates to the form state without wiping other existing fields.
3. **Delete Field**: A rule-based tool that scans for omission keywords (like "remove samples" or "clear attendees") and clears those precise variables from the state.
4. **Get Form**: Returns the current multi-turn interaction state so it can be visually synchronized via Redux on the client interface.
5. **Validate Form**: Checks the accumulated state against required constraints (HCP Name, Date, Time) and blocks database submission until missing variables are provided.
6. **Submit Interaction**: Binds the validated global memory state to the SQLAlchemy session and commits the final interaction log into the PostgreSQL database.

## Tech Stack
- **Frontend**: React UI, Redux, Google Inter Font
- **Backend API**: Python, FastAPI
- **AI Agent Framework**: LangGraph, LangChain Core
- **Language Model**: Groq API (llama-3.3-70b-versatile, selected primarily due to external model deprecations)
- **Database**: PostgreSQL, SQLAlchemy ORM

## Project Structure
```text
backend/
├── agent/
│   ├── graph.py           # LangGraph state machine configuration
│   ├── llm.py             # LLM provider initialization
│   ├── state.py           # State management logic
│   └── tools.py           # Implementation of agent tools
├── db/
│   ├── database.py        # SQLAlchemy session initialization
│   └── models.py          # Database schema definitions
├── frontend/
│   ├── public/
│   └── src/               
│       ├── App.js         # Chat interface and form view components
│       └── store.js       # Redux state configuration
├── schemas/
│   └── interaction.py     # Data validation schemas
├── main.py                # Server entry point
├── config.py              # Environment variable loading
├── requirements.txt       # Python dependency definitions
└── .env                   # Configuration secrets
```

## Setup Instructions

1. Configure the database connection by creating a `.env` file in the root directory:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=crm_db
GROQ_API_KEY=your_groq_api_key
```

2. Start a PostgreSQL instance matching your configurations.

3. Initialize the backend:
```bash
cd backend
python -m venv venv
# On Windows use: venv\Scripts\activate
# On Unix use: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
The server will run on port 8000.

4. Initialize the frontend:
```bash
cd frontend
npm install
npm start
```
The client will run on port 3000.

## Usage
Open the application in a browser at `http://localhost:3000`.
The interface is split into two panes. The right pane is a chat window where you submit logs. The left pane visually reflects the parsed state of the data payload.

Example workflow:
1. Enter "Met Dr. Smith at 2 PM today" into the chat interface. Wait for the left panel to populate the doctor name, time, and date fields.
2. Append data by saying "Also discussed standard insulin dosing". The topics field will populate.
3. Correct data by saying "Change the time to 4 PM". The form state updates safely.
4. Tell the agent to "Submit the interaction" once the mandatory fields are populated.

## Design Decisions
- **Hybrid Intent Routing**: The router validates intent using string matching and regex before querying the LLM. This reduces inference compute delays. LLMs are leveraged exclusively for complex entity extraction.
- **Model Selection Priority**: While Groq's gemma2-9b-it handles basic chatting well, llama-3.3-70b-versatile was required to consistently enforce strict JSON schema parsing and extraction logic.
- **Intermediate State**: Mapped entities are held in an intermediate memory state rather than writing directly to the database. This allows users to iteratively review and retract information before executing a hard database commit.

## Limitations
- **Concurrency Overwrites**: The global `FORM_STATE` dictionary in `state.py` handles exactly one concurrent user session. Simultaneous inputs from multiple users will overwrite each other. True multi-tenancy requires mapping session IDs to isolated state stores.
- **Regex Dependency**: Basic entities like dates and times rely heavily on hardcoded regex patterns instead of true semantic entity resolution, making the extraction brittle against varied phrasing formats.
- **Ephemeral State Memory**: Because the intermediate state is kept in server memory pending save, any backend restart drops the entire in-progress form, requiring the representative to start over.

## Future Improvements
- Implement isolated conversation sessions indexed by user ID to support concurrent interactions.
- Adopt a strict Named Entity Recognition (NER) pipeline for base field extraction to reduce the dependency on static regex rules.
- Transition intermediate state storage from local memory over to an external caching layer like Redis to survive unexpected server reboots.

## Conclusion
This CRM interface replaces static data entry forms with a conversational chat log that parses context securely into a database schema. The result removes operational friction from medical reporting and ensures strict data integrity.
