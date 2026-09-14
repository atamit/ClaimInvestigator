import json
import os
import uuid

import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from claim_agent import investigate_claim

load_dotenv()
app = FastAPI(title="ClaimInvestigator API")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AGENTCORE_RUNTIME_ARN = os.getenv("AGENTCORE_RUNTIME_ARN")
aws_session = boto3.Session(
    region_name=AWS_REGION
)
# agentcore = boto3.client(
#     "bedrock-agentcore",
#     region_name=AWS_REGION,
# )
agentcore = aws_session.client(
    "bedrock-agentcore"
)

# @app.post("/investigate")
# def investigate(claim_id: str):
#     return investigate_claim(claim_id)

@app.post("/investigate")
def investigate(claim_id: str):

    if not AGENTCORE_RUNTIME_ARN:
        raise HTTPException(
            status_code=500,
            detail="AGENTCORE_RUNTIME_ARN is not configured."
        )

    try:
        response = agentcore.invoke_agent_runtime(
            agentRuntimeArn=AGENTCORE_RUNTIME_ARN,
            runtimeSessionId=str(uuid.uuid4()),
            payload=json.dumps({
                "claim_id": claim_id
            }).encode("utf-8"),
            qualifier="DEFAULT",
        )

        chunks = []

        for chunk in response.get("response", []):
            chunks.append(chunk.decode("utf-8"))

        result = json.loads("".join(chunks))

        return result

    except Exception as exc:
        print(f"\nAgentCore invocation failed: {repr(exc)}\n")

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


app.mount("/", StaticFiles(directory="static", html=True), name="static")