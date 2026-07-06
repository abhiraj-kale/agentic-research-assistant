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

# --- Workaround for crewAI issue #5886 (open upstream): CrewAI injects a
# `cache_breakpoint` marker into system messages that non-Anthropic providers
# (Mistral, Groq) reject with a 400 error. Neutralizing the injector lets every
# provider in the pool work. Defensive: no-op if the internal API changes. ---
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg, *a, **k: msg
    print("[startup] crewAI #5886 cache_breakpoint patch applied")
except Exception as _e:
    print(f"[startup] cache_breakpoint patch NOT applied: {_e}")

# --- LLM CONFIGURATION: full multi-provider fallback chain. The cache_breakpoint
# bug that used to make Mistral/Groq fail is neutralized by the patch above. ---
llm_pool = [
    LLM(model="gemini/gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY")),
    LLM(model="mistral/mistral-large-latest", api_key=os.getenv("MISTRAL_API_KEY")),
    LLM(model="groq/llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY")),
    LLM(model="groq/llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY")),
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

# --- HEALTH / KEEP-ALIVE (pinged on a schedule so the free-tier instance
# does not sleep during Chrome Web Store review). Intentionally lightweight:
# it returns immediately and never touches the LLM/agent machinery. ---
@app.get("/health")
async def health():
    return {"status": "ok"}

# --- TEMPORARY DIAGNOSTIC: runs a minimal real crew on each model in the pool
# so we can confirm every provider works after the cache_breakpoint patch.
# Remove this endpoint once verified. ---
@app.get("/diag")
async def diag():
    import importlib.metadata as _md
    versions = {}
    for pkg in ("crewai", "crewai-tools", "litellm", "openai"):
        try:
            versions[pkg] = _md.version(pkg)
        except Exception:
            versions[pkg] = "n/a"
    results = []
    for llm in llm_pool:
        try:
            agent = Agent(role="Tester", goal="Reply briefly",
                          backstory="You reply concisely.", llm=llm, allow_delegation=False)
            task = Task(description="Reply with the single word OK.",
                        expected_output="OK", agent=agent)
            crew = Crew(agents=[agent], tasks=[task])
            out = await asyncio.to_thread(crew.kickoff)
            results.append({"model": llm.model, "ok": True, "sample": str(out)[:60]})
        except Exception as e:
            results.append({"model": llm.model, "ok": False,
                            "error": f"{type(e).__name__}: {str(e)[:250]}"})
    return {"versions": versions, "results": results}

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
                # Full detail to server logs; users see a friendly message.
                print(f"Attempt {attempt + 1} failed: {type(e).__name__}: {e}")

                if attempt == len(llm_pool) - 1:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Service temporarily unavailable. Please try again in a moment.'})}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'progress', 'message': '⚠️ Switching to a backup AI model...'})}\n\n"
                    await asyncio.sleep(1)

    # Return the stream directly to the client
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)