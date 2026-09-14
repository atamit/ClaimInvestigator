


ClaimInvestigator
AI-powered transaction dispute investigation with Strands Agents and Amazon Bedrock AgentCore
ClaimInvestigator is an agentic transaction-dispute investigation application that performs a multi-step investigation from a single Claim ID.

Using Strands Agents, the application retrieves claim information, loads the applicable investigation procedure, gathers evidence, validates investigation completeness, and produces an investigation summary.

The deployed application runs on Amazon Bedrock AgentCore Runtime and uses AgentCore Identity for secure outbound authentication to Claude.

The LLM investigates; deterministic business rules control the financial recommendation.

Why I built this
Transaction-dispute investigations require significant manual effort before a decision can be made.

For an ACH or ATM dispute, an investigator may need to:

retrieve the claim,

identify the correct investigation procedure,

review transaction activity,

verify customer authorization,

gather supporting evidence,

confirm that every required investigation step was completed.

ClaimInvestigator explores how an AI agent can perform this investigative work end to end while keeping consequential financial decisions outside the LLM.

What it does
An analyst enters a Claim ID.

ClaimInvestigator then:

Retrieves the claim and identifies the dispute type.

Loads the applicable investigation procedure from Amazon S3.

Determines the required investigative checks.

Calls tools to gather transaction and authorization evidence.

Performs the investigation.

Validates that all required checks were completed.

Produces a structured investigation summary.

Passes validated findings to deterministic Python business rules.

Returns the recommendation with an auditable tool-call history.

The analyst does not need to manually prompt the agent through each step.

Claim ID → Investigate → Review findings and recommendation

Demo scenario
The primary demo uses:

Claim: CLM002
Type: ACH
Claim amount: $75,000

The investigation finds:

two $75,000 ACH transactions,

the same transaction originator,

$150,000 of transaction activity reviewed,

customer authorization reported as false,

all required ACH investigation checks completed.

The validated findings are then passed to deterministic business rules for the final recommendation.

All claim and transaction data in this repository are simulated.

Architecture
Analyst
   |
   v
Web UI
   |
   v
FastAPI
   |
   v
InvokeAgentRuntime
   |
   v
Amazon Bedrock AgentCore Runtime
   |
   v
main.py
   |
   v
Strands Agent
   |
   +-----------------------------+
   |                             |
   v                             v
Investigation Tools       Procedure / Evidence Sources
   |                             |
   |                       Amazon S3 Procedures
   |                       Simulated Claim Data
   |
   v
Investigation Completeness Validation
   |
   v
Deterministic Business Rules
   |
   v
Investigation Result
Outbound model authentication:

AgentCore Runtime
       |
       v
AgentCore Identity
       |
       v
Anthropic API Credential
       |
       v
Claude
See:

docs/claiminvestigator-architecture.png

Key design principle
ClaimInvestigator deliberately separates investigation from financial decisioning.

Agentic layer
The Strands agent:

interprets the claim,

determines what evidence is required,

selects and calls tools,

follows the investigation procedure,

analyzes evidence,

creates the investigation summary.

Deterministic layer
Python business rules:

verify investigation completeness,

evaluate validated evidence,

produce the recommendation,

determine the refund amount.

The LLM is explicitly instructed not to approve claims or determine refund amounts.

This preserves the flexibility of an AI agent while maintaining a controlled boundary around consequential decisions.

Technology stack
Strands Agents — agent orchestration and tool execution

Amazon Bedrock AgentCore Runtime — deployed agent runtime

AgentCore Identity — secure outbound authentication

Claude — language model

Amazon S3 — investigation procedure storage

Python — agent, tools, validation, and business rules

FastAPI — web/API backend

HTML / CSS / JavaScript — analyst-facing UI

AWS IAM — runtime and invocation permissions

Strands tools
The agent uses:

get_claim

get_procedure

get_transaction_history

check_customer_authorization

validate_investigation_completeness

get_claim
Retrieves the claim and identifies the dispute type.

get_procedure
Loads the applicable ACH or ATM investigation procedure from Amazon S3.

get_transaction_history
Retrieves transaction evidence associated with the claim.

check_customer_authorization
Retrieves whether the customer reported authorizing the disputed transaction.

validate_investigation_completeness
Compares completed investigation checks against the checks required by the applicable procedure.

The validator fails closed if the procedure cannot be retrieved or contains no required checks.

Project structure
ClaimInvestigator/
│
├── app.py
├── main.py
├── claim_agent.py
├── tools.py
├── requirements.txt
├── requirements-agentcore.txt
├── README.md
├── LICENSE
├── .gitignore
│
├── static/
│   └── index.html
│
├── procedures/
│   ├── ACH.json
│   └── ATM.json
│
└── docs/
    └── claiminvestigator-architecture.png
Prerequisites
For local development:

Python 3.12+

AWS account

Amazon S3 bucket containing investigation procedures

AWS credentials permitted to invoke the deployed AgentCore Runtime

For AgentCore deployment:

Amazon Bedrock AgentCore Runtime

AgentCore Identity outbound-auth provider

Anthropic API key stored through AgentCore Identity

AgentCore execution role with access to the procedure S3 bucket

Installation
Clone the repository:

git clone https://github.com/atamit/ClaimInvestigator.git
cd ClaimInvestigator
Create a virtual environment.

Windows
python -m venv .venv
.venv\Scripts\activate
macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
Install dependencies:

pip install -r requirements.txt
Local environment
Create a .env file in the project root:

AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AGENTCORE_RUNTIME_ARN=your_agentcore_runtime_arn
Do not commit .env.

The repository .gitignore should include:

.env
.venv/
__pycache__/
*.pyc
deployment_package/
*.zip
Amazon S3 procedure setup
Investigation procedures are stored under:

procedures/
Example:

s3://<your-bucket>/procedures/ACH.json
s3://<your-bucket>/procedures/ATM.json
Example ACH procedure:

{
  "claim_type": "ACH",
  "checks": [
    {
      "check": "Verify ACH transaction details",
      "tool": "get_transaction_history"
    },
    {
      "check": "Check transaction originator",
      "tool": "get_transaction_history"
    },
    {
      "check": "Check customer account activity",
      "tool": "get_transaction_history"
    },
    {
      "check": "Check whether the customer authorized the transaction",
      "tool": "check_customer_authorization"
    }
  ]
}
Run the web application
Start FastAPI:

uvicorn app:app --reload
Open:

http://127.0.0.1:8000
Enter:

CLM002
and click Investigate Claim.

The request flow is:

Browser
  → FastAPI
  → AgentCore Runtime
  → Strands Agent
  → Tools / S3
  → Validation
  → Deterministic recommendation
API
Endpoint:

POST /investigate?claim_id=CLM002
Example:

curl -X POST "http://127.0.0.1:8000/investigate?claim_id=CLM002"
The response includes:

claim ID

claim type

customer

investigation summary

authorization evidence

completeness validation

recommendation

tool-call history

Amazon Bedrock AgentCore
The deployed agent runs inside Amazon Bedrock AgentCore Runtime.

main.py provides the AgentCore entry point and invokes the ClaimInvestigator workflow.

AgentCore provides the hosted execution environment, while AgentCore Identity securely supplies the Anthropic API credential used by the deployed agent.

The FastAPI application invokes the runtime using:

bedrock-agentcore:InvokeAgentRuntime
AWS credentials and model API keys remain server-side and are never exposed to the browser.

Current limitations
ClaimInvestigator is a hackathon demonstration and is not intended for production financial decisioning.

Current limitations include:

simulated claim and transaction data,

ACH and ATM procedures only,

simplified deterministic recommendation rules,

no production banking-system integrations,

no authentication or role-based access control,

no persistent investigation-result store.

What's next
Future improvements include:

additional dispute types,

integration with banking transaction and case-management systems,

human-in-the-loop review and approval,

persistent evidence and investigation history,

procedure versioning and governance,

richer anomaly detection,

authentication and role-based access control,

production observability and tracing.

The longer-term goal is an agentic investigation layer for financial operations, where AI agents perform repetitive investigative work while deterministic controls and people retain authority over consequential decisions.

Security
Never commit:

.env

AWS credentials

Anthropic API keys

local virtual environments

AgentCore deployment packages

production claim or customer data

All data included in this repository is simulated.

License
Released under the MIT License.