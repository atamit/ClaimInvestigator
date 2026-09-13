ClaimInvestigator

AI-powered transaction dispute investigation with Strands Agents

ClaimInvestigator is an agentic transaction-dispute investigation application that performs a multi-step investigation from a single Claim ID.

The application uses Strands Agents to retrieve claim information, load the applicable investigation procedure, gather supporting evidence, validate that the required checks were completed, and produce an investigation summary.

A key design principle is that the LLM performs investigation and evidence synthesis, while deterministic business rules control the final financial recommendation.

Why I built this

Transaction-dispute investigation is a good example of a workflow where a significant amount of effort is spent gathering information before a decision can be made.

For an ACH or ATM dispute, an investigator may need to:

retrieve the claim,

determine the correct investigation procedure,

review transaction history,

verify customer authorization,

gather supporting evidence,

and ensure every required check has been completed.

I wanted to explore whether an AI agent could perform this investigation work end to end without giving the LLM unrestricted authority over a financial decision.

ClaimInvestigator was built to demonstrate that separation.

What it does

An analyst enters a Claim ID.

ClaimInvestigator then:

Retrieves the claim and identifies the dispute type.

Loads the applicable investigation procedure from Amazon S3.

Determines the investigative actions required by that procedure.

Calls tools to retrieve transaction history and customer-authorization evidence.

Performs the required investigation checks.

Validates that the investigation is complete.

Produces a structured investigation summary.

Passes the validated findings to deterministic business rules.

Returns the recommendation together with an audit trail of the tool calls.

The analyst does not need to manually prompt the agent through each step.

Enter Claim ID → Investigate → Review findings and recommendation

Demo scenario

The main demo uses claim:

CLM002

This is an ACH dispute for $75,000.

During the investigation, ClaimInvestigator finds:

two $75,000 ACH transactions,

the same transaction originator,

$150,000 of transaction activity associated with the investigation,

customer authorization marked as false,

and all required ACH investigation checks completed.

The validated investigation is then passed to deterministic business rules for the final recommendation.

The sample claim and transaction data in this repository are simulated for demonstration purposes.

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
Strands Agent
   |
   +-------------------------------+
   |                               |
   v                               v
Investigation Tools         Procedure / Evidence Sources
   |                               |
   |                        Amazon S3 Procedures
   |                        Claim / Transaction Data
   |
   v
Investigation Completeness Validation
   |
   v
Deterministic Business Rules
   |
   v
Final Investigation Result

Key design principle

The LLM performs investigation and evidence synthesis. Final financial decisions are produced by deterministic business rules.

The LLM is responsible for investigation orchestration, tool use, evidence analysis, and summarization.

It is explicitly not responsible for directly approving a claim or deciding the refund amount.

Technology stack

Strands Agents — agent orchestration and tool execution

Claude — language model used during development

Amazon S3 — storage for investigation procedures

Python — agent, tools, validation, and business rules

FastAPI — backend API

HTML / CSS / JavaScript — analyst-facing UI

Strands tools

The agent currently uses the following tools:

get_claim
get_procedure
get_transaction_history
check_customer_authorization
validate_investigation_completeness

get_claim

Retrieves the claim and determines the claim type.

get_procedure

Loads the applicable investigation procedure from Amazon S3.

Example procedure files:

ACH.json
ATM.json

get_transaction_history

Retrieves transaction evidence associated with the claim.

check_customer_authorization

Retrieves whether the customer reported authorizing the disputed transaction.

validate_investigation_completeness

Compares the completed investigation checks with the checks required by the applicable procedure.

Project structure

ClaimInvestigator/
├── claim_agent.py
├── tools.py
├── api.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── static/
│   └── index.html
├── procedures/
│   ├── ACH.json
│   └── ATM.json
└── docs/
    └── claiminvestigator-architecture.png

Prerequisites

Python 3.12 recommended

AWS account with access to Amazon S3

Anthropic API key

An S3 bucket containing the investigation procedure JSON files

Installation

Clone the repository:

git clone <YOUR_PUBLIC_REPOSITORY_URL>
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

Environment variables

Create a .env file in the project root.

ANTHROPIC_API_KEY=your_anthropic_api_key

AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1

Do not commit the .env file.

The repository should include:

.env
.venv/
__pycache__/
*.pyc

Amazon S3 procedure setup

ClaimInvestigator loads investigation procedures from Amazon S3.

Create an S3 bucket and upload the procedure files under:

procedures/

For example:

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

Update the S3 bucket configuration in the application for your environment before running the project.

Run the agent directly

To run the current demonstration from Python:

python claim_agent.py

The default demonstration uses:

CLM002

Run the web application

Start FastAPI:

uvicorn api:app --reload

Open:

http://127.0.0.1:8000

Enter:

CLM002

and click Investigate Claim.

API

The application exposes:

POST /investigate?claim_id=CLM002

Example:

curl -X POST "http://127.0.0.1:8000/investigate?claim_id=CLM002"

The response contains:

claim ID,

claim type,

customer,

investigation summary,

authorization evidence,

completeness validation,

recommendation,

and tool-call history.

Why the decision logic is separate from the LLM

ClaimInvestigator deliberately separates two responsibilities.

Agentic layer

The Strands agent:

interprets the claim,

determines what evidence is needed,

selects tools,

gathers evidence,

follows the investigation procedure,

and creates an investigation summary.

Deterministic layer

Python business rules:

verify that the investigation is complete,

evaluate validated evidence,

produce the final recommendation,

and determine the refund amount.

This architecture keeps the flexibility of an AI agent while providing a controlled boundary around consequential financial decisions.

Current limitations

This project is a hackathon demonstration and is not intended for production financial decisioning.

Current limitations include:

simulated claim and transaction data,

a limited set of ACH and ATM procedures,

simplified deterministic recommendation rules,

no authentication or role-based access control,

no integration with a production banking or case-management platform,

and no persistent investigation-result store.

What's next

Planned improvements include:

deployment using Amazon Bedrock AgentCore,

additional dispute types,

integration with transaction and case-management systems,

human-in-the-loop review and approval,

persisted investigation evidence and results,

procedure versioning and governance,

expanded anomaly detection,

authentication and role-based access control,

and production-grade observability and tracing.

The longer-term direction is an agentic investigation layer for financial operations where agents perform repetitive investigative work while deterministic controls and people retain authority over consequential decisions.

Security note

Never commit:

.env

AWS credentials

Anthropic API keys

local virtual environments

production claim or customer data

The data included in this project is simulated.

License

This project is intended to be released under the MIT License for the Agents for Humans hackathon.

See  https://chatgpt.com/c/LICENSE