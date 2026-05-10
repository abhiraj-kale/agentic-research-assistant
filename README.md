# 🔍 Agentic Research Assistant

**Agentic Research Assistant** is a professional-grade browser extension and distributed backend system that orchestrates a multi-agent "Crew" to perform autonomous web research and document synthesis. 

Unlike standard AI wrappers, this system utilizes an event-driven architecture to stream real-time agent reasoning directly to the user's side panel.



## 🛠️ System Architecture

1. **Client (Chrome Extension):** Built with Manifest V3, utilizing the `sidePanel` and `scripting` APIs to interact with active browser tabs.
2. **Real-Time Telemetry:** Implements **Server-Sent Events (SSE)** via FastAPI to provide a "live" log of agent thought processes, preventing UI hang during long-running tasks.
3. **Multi-Agent Orchestration:** Powered by **CrewAI**, separating concerns between a **Research Analyst** (data gathering) and a **Technical Auditor** (quality control and formatting).
4. **LLM Resilience:** Features a fallback rotation pool across **Groq (Llama 3.3)** and **Mistral AI** to ensure 99.9% uptime during API rate-limiting.

## 🚀 Key Features

- **Autonomous Research:** Leverages **Tavily AI** for high-fidelity, real-time web scraping and data retrieval.
- **Context-Aware Summarization:** Dynamically extracts DOM content from the active tab for immediate synthesis.
- **Streaming UI:** A monospace terminal-style log window that appends live status updates from the backend.
- **Automated Reporting:** Generates professionally branded, standardized PDF reports using a custom Markdown-to-HTML rendering engine.

## 🏁 Getting Started

### Backend Setup
1. Navigate to `/backend`
2. Create a `.env` file with your `GROQ_API_KEY`, `MISTRAL_API_KEY`, and `TAVILY_API_KEY`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python main.py`

### Extension Setup
1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer Mode**.
3. Click **Load Unpacked** and select the `/extension` folder.
4. Open the Side Panel to begin.

## 📄 License
MIT