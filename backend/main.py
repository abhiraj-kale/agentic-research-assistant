import os
import json
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from crewai import Agent, Task, Crew, LLM
from crewai_tools import TavilySearchTool

load_dotenv()

# --- LLM CONFIGURATION ---
# I fixed the order here: Mistral is now truly the first item (Index 0)
# --- LLM CONFIGURATION ---
llm_pool = [
    # 1. Primary: Gemini 2.5 Flash (Lightning fast, huge context window, perfect for research)
    LLM(model="gemini/gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY")),

    # 2. Secondary: Mistral Large (Flawless fallback for tool calling)
    LLM(model="mistral/mistral-large-latest", api_key=os.getenv("MISTRAL_API_KEY")),
    
    # 3. Tertiary: Llama 3.1 8B (Fast and reliable Groq fallback)
    LLM(model="groq/llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY")),
    
    # 4. Last Resort: Llama 3.3 70B 
    LLM(model="groq/llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
]

search_tool = TavilySearchTool()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    topic: str = None
    textToSummarize: str = None

# --- PRIVACY POLICY (served for the Chrome Web Store listing) ---
PRIVACY_HTML_PATH = os.path.join(os.path.dirname(__file__), "privacy.html")

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    with open(PRIVACY_HTML_PATH, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Notice: current_llm_index = 0 is GONE from here

@app.post("/research")
async def start_research(request: ResearchRequest):
    is_summarization = bool(request.textToSummarize)
    target_content = request.textToSummarize if is_summarization else request.topic

    if not target_content:
        raise HTTPException(status_code=400, detail="No topic or text provided")

    # --- ASYNC GENERATOR FOR STREAMING ---
    async def event_generator():
        # Notice: global current_llm_index is GONE from here
        
        for attempt in range(len(llm_pool)):
            try:
                # 1. Send initialization status
                yield f"data: {json.dumps({'status': 'progress', 'message': '🚀 Initializing AI Agents...'})}\n\n"
                await asyncio.sleep(0.5)

                if is_summarization:
                    yield f"data: {json.dumps({'status': 'progress', 'message': '📄 Reading and analyzing page content deeply...'})}\n\n"
                else:
                    search_msg = f'🔍 Searching the web for insights on "{target_content}"...'
                    yield f"data: {json.dumps({'status': 'progress', 'message': search_msg})}\n\n"
                await asyncio.sleep(0.5)

                # Now we strictly use the 'attempt' variable!
                primary_llm = llm_pool[attempt % len(llm_pool)]
                secondary_llm = llm_pool[(attempt + 1) % len(llm_pool)]

                # SETUP AGENTS
                researcher = Agent(
                    role='Analyst', 
                    goal='Analyze and extract deep insights from the provided input.',
                    backstory='You are an expert at synthesizing information. You can search the web if needed or summarize long documents with high precision.',
                    tools=[search_tool] if not is_summarization else [], 
                    llm=primary_llm,
                    max_iter=3,
                    allow_delegation=False
                )

                auditor = Agent(
                    role='Auditor', 
                    goal='Format text into strict, numbered Markdown.',
                    backstory="""You are a technical editor. You ensure reports are professional, 
                    properly spaced, and strictly use numbered lists instead of bullets.""",
                    llm=secondary_llm,
                    allow_delegation=False
                )

                # SETUP TASKS
                if is_summarization:
                    t1_desc = f"Thoroughly summarize the following text. Focus on key arguments, data points, and conclusions: {target_content}"
                    t1_expected = "A comprehensive, high-level summary of the provided text."
                else:
                    t1_desc = f"Conduct deep-dive research on '{target_content}'. Find history, current trends, and technical details."
                    t1_expected = "Extensive research findings with multiple detailed sections."

                t1 = Task(description=t1_desc, expected_output=t1_expected, agent=researcher)

                t2 = Task(
                    description="""Format the output into a clean Markdown report.
                    RULES:
                    1. Use '# ' for the main title and '## ' for section headings.
                    2. ALWAYS leave a blank line before and after every heading.
                    3. Use ONLY numbered lists (1., 2., 3.) for all lists. No bullet points.
                    4. DO NOT use code blocks (```).""", 
                    expected_output="A professionally formatted Markdown string.", 
                    agent=auditor
                )

                crew = Crew(agents=[researcher, auditor], tasks=[t1, t2])
                
                yield f"data: {json.dumps({'status': 'progress', 'message': '🧠 Agents are collaborating on the final report...'})}\n\n"
                
                # RUN CREW IN A BACKGROUND THREAD to prevent blocking the async stream
                result = await asyncio.to_thread(crew.kickoff)
                
                yield f"data: {json.dumps({'status': 'progress', 'message': '✅ Formatting complete! Generating PDF...'})}\n\n"
                await asyncio.sleep(0.5)

                # 2. Send final completion payload
                yield f"data: {json.dumps({'status': 'complete', 'content': str(result)})}\n\n"
                break  # Break out of the retry loop on success

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                # Notice: current_llm_index += 1 is GONE from here!
                
                if attempt == len(llm_pool) - 1:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Service temporarily unavailable.'})}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'progress', 'message': '⚠️ Server overload. Switching to backup AI model...'})}\n\n"
                    await asyncio.sleep(1)

    # Return the stream directly to the client
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)