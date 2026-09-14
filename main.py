from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    from claim_agent import investigate_claim
    claim_id = payload.get("claim_id", "CLM002")
    return investigate_claim(claim_id)

if __name__ == "__main__":
    app.run()