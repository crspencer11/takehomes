from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from parallel import Parallel
from parallel.types import TaskSpecParam

from datetime import datetime
import os

app = FastAPI()

# allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
client = Parallel(api_key=os.environ["PARALLEL_API_KEY"])

class SearchRequest(BaseModel):
    query: str
    mode: str = "fast"

feedback_store = []
class FeedbackRequest(BaseModel):
    url: str
    is_correct: bool

@app.get("/")
async def home():
    return FileResponse("../frontend/index.html")

@app.post("/search")
async def search(req: SearchRequest):
    response = client.beta.search(
        objective=f"Find information about: {req.query}",
        search_queries=[req.query],
        mode=req.mode,
        excerpts={"max_chars_per_result": 2000}
    )
    return {"results": response.results}

@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    print(req)
    entry = req.model_dump()
    print(entry)
    entry["timestamp"] = datetime.utcnow().isoformat()

    feedback_store.append(entry)
    return {"status": "ok", "stored": entry}

@app.post("/compare")
async def compare(req: SearchRequest):
    fast_mode = client.beta.search(
        objective=f"Find information about: {req.query}",
        search_queries=[req.query],
        mode="fast",
    )

    agentic_mode = client.beta.search(
        objective=f"Find information about: {req.query}",
        search_queries=[req.query],
        mode="agentic",
    )

    one_shot_mode = client.beta.search(
        objective=f"Find information about: {req.query}",
        search_queries=[req.query],
        mode="agentic",
    )

    return {
        "fast": fast_mode.results,
        "agentic": agentic_mode.results,
        "one_shot": one_shot_mode.results,
    }