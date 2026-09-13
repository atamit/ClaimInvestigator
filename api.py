from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from claim_agent import investigate_claim

app = FastAPI(title="ClaimInvestigator API")


@app.post("/investigate")
def investigate(claim_id: str):
    return investigate_claim(claim_id)

app.mount("/", StaticFiles(directory="static", html=True), name="static")