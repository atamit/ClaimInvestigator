from strands import tool
import boto3
import json
from dotenv import load_dotenv
load_dotenv()
import os
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX", "procedures/")
s3 = boto3.client("s3")

@tool
def get_claim(claim_id: str) -> dict:
    """
    Retrieve claim information using a claim ID.

    Args:
        claim_id: The ID of the claim to retrieve.

    Returns:
        Claim details.
    """
    print(f"TOOL CALLED: claim_id=[{claim_id}]")
    claims = {
        "CLM001": {
            "claim_id": "CLM001",
            "claim_type": "ATM",
            "amount": 25000,
            "customer": "John",
            "status": "OPEN",
        },
        "CLM002": {
            "claim_id": "CLM002",
            "claim_type": "ACH",
            "amount": 75000,
            "customer": "Sarah",
            "status": "OPEN",
        },
    }

    return claims.get(
        claim_id,
        {
            "claim_id": claim_id,
            "error": "Claim not found",
        },
    )

@tool
def get_procedure_local(claim_type: str) -> dict:
    """
    Retrieve the investigation procedure for a claim type.

    Args:
        claim_type: The type of claim, such as ATM or ACH.

    Returns:
        Investigation procedure for that claim type.
    """

    print(f"TOOL CALLED: claim_type=[{claim_type}]")
    procedures = {
        "ATM": {
            "claim_type": "ATM",
            "checks": [
                {
                    "check": "Verify ATM transaction details",
                    "tool": "get_transaction_history"
                },
                {
                    "check": "Check whether the customer was present at the ATM",
                    "tool": "get_transaction_history"
                },
                {
                    "check": "Check transaction timestamp and location",
                    "tool": "get_transaction_history"
                },
                {
                    "check": "Check whether the card was reported lost or stolen",
                    "tool": "get_transaction_history"
                }
            ]
        },
        "ACH": {
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
            ],
        },
    }

    return procedures.get(
        claim_type,
        {
            "claim_type": claim_type,
            "error": "No procedure found for this claim type",
        },
    )


@tool
def get_procedure(claim_type: str) -> dict:
    """
    Retrieve the investigation procedure for a claim type from S3.

    Args:
        claim_type: The type of claim, such as ATM or ACH.

    Returns:
        Investigation procedure for that claim type.
    """

    print(f"TOOL CALLED - get_procedure : claim_type=[{claim_type}]")

    key = f"{S3_PREFIX}{claim_type.upper()}.json"

    try:
        response = s3.get_object(
            Bucket=S3_BUCKET,
            Key=key,
        )

        procedure = json.loads(
            response["Body"].read().decode("utf-8")
        )

        print(f"S3 PROCEDURE LOADED: s3://{S3_BUCKET}/{key}")

        return procedure

    except Exception as e:
        print(f"S3 PROCEDURE ERROR: {e}")

        return {
            "claim_type": claim_type,
            "error": f"Unable to retrieve procedure: {str(e)}",
        }

    
@tool
def get_transaction_history(claim_id: str) -> dict:
    """
    Retrieve recent transaction history related to a claim.

    Args:
        claim_id: The ID of the claim.

    Returns:
        Recent transaction history.
    """
    print(f"TOOL CALLED: claim_id=[{claim_id}]")

    history = {
        "CLM001": [
            {
                "transaction_id": "TX1001",
                "type": "ATM",
                "amount": 25000,
                "location": "Bangalore",
                "status": "DECLINED",
            },
            {
                "transaction_id": "TX1002",
                "type": "ATM",
                "amount": 25000,
                "location": "Bangalore",
                "status": "SUCCESS",
            },
        ],
        "CLM002": [
            {
                "transaction_id": "TX2001",
                "type": "ACH",
                "amount": 75000,
                "originator": "ABC Services",
                "status": "SUCCESS",
            },
            {
                "transaction_id": "TX2002",
                "type": "ACH",
                "amount": 75000,
                "originator": "ABC Services",
                "status": "SUCCESS",
            },
        ],
    }

    return {
        "claim_id": claim_id,
        "transactions": history.get(claim_id, []),
    }

@tool
def check_customer_authorization(claim_id: str) -> dict:
    """
    Check whether the customer authorized the claimed transaction.

    Args:
        claim_id: The ID of the claim.

    Returns:
        Customer authorization information.
    """
    print(f"TOOL CALLED - check_customer_authorization: claim_id=[{claim_id}]")

    authorization = {
        "CLM001": {
            "authorized": True,
            "source": "Customer confirmation",
        },
        "CLM002": {
            "authorized": False,
            "source": "Customer confirmation",
        },
    }

    return {
        "claim_id": claim_id,
        **authorization.get(
            claim_id,
            {
                "authorized": None,
                "source": "No authorization data available",
            },
        ),
    }

@tool
def validate_investigation_completeness(
    procedure: dict,
    completed_checks: list[str],
) -> dict:
    """
    Validate whether all required investigation checks have been completed.

    Args:
        procedure: Investigation procedure containing required checks.
        completed_checks: Names of checks that have been completed.

    Returns:
        Validation result showing completed and missing checks.
    """

    print(f"TOOL CALLED - validate_investigation_completeness: completed_checks=[{completed_checks}]")
    required_checks = [
        check["check"]
        for check in procedure.get("checks", [])
    ]

    missing_checks = [
        check
        for check in required_checks
        if check not in completed_checks
    ]

    return {
        "complete": len(missing_checks) == 0,
        "required_checks": required_checks,
        "completed_checks": completed_checks,
        "missing_checks": missing_checks,
    }

def make_recommendation(claim: dict, authorization: dict, validation: dict) -> dict:
    """
    Apply deterministic business rules to produce the final recommendation.
    """

    if not validation["complete"]:
        return {
            "decision": "INVESTIGATION INCOMPLETE",
            "refund_amount": 0,
            "reason": "All required investigation checks have not been completed.",
        }

    if authorization.get("authorized") is False:
        return {
            "decision": "APPROVE CLAIM",
            "refund_amount": claim["amount"],
            "reason": "Customer did not authorize the transaction.",
        }

    if authorization.get("authorized") is True:
        return {
            "decision": "DENY CLAIM",
            "refund_amount": 0,
            "reason": "Customer authorized the transaction.",
        }

    return {
        "decision": "MANUAL REVIEW",
        "refund_amount": 0,
        "reason": "Customer authorization could not be determined.",
    }
if __name__ == "__main__":
    print(get_claim("CLM001"))
    print(get_procedure("ACH"))
    # print(get_transaction_history("CLM002"))
    # print(check_customer_authorization("CLM002"))
    # print(make_recommendation)

# if __name__ == "__main__":
#     procedure = {
#         "checks": [
#             {"check": "Verify ACH transaction details"},
#             {"check": "Check transaction originator"},
#             {"check": "Check customer account activity"},
#             {"check": "Check whether the customer authorized the transaction"},
#         ]
#     }

#     completed_checks = [
#         "Verify ACH transaction details",
#         "Check transaction originator",
#         "Check customer account activity",
#         "Check whether the customer authorized the transaction",
#     ]

#     result = validate_investigation_completeness(
#         procedure,
#         completed_checks,
#     )

#     print(result)


# if __name__ == "__main__":
    claim = get_claim("CLM002")

    authorization = check_customer_authorization("CLM002")

    procedure = get_procedure("ACH")

    completed_checks = [
        "Verify ACH transaction details",
        "Check transaction originator",
        "Check customer account activity",
        "Check whether the customer authorized the transaction",
    ]

    validation = validate_investigation_completeness(
        procedure,
        completed_checks,
    )

    recommendation = make_recommendation(
        claim,
        authorization,
        validation,
    )

    print("\n========== RECOMMENDATION ==========")
    print(recommendation)