from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.hooks import (BeforeModelCallEvent, AfterModelCallEvent, BeforeToolCallEvent, AfterToolCallEvent)

from tools import get_claim, get_procedure, get_transaction_history,check_customer_authorization,validate_investigation_completeness, make_recommendation
import json


model= AnthropicModel(
    client_args={
        "api_key":None
    },
    model_id="claude-haiku-4-5-20251001",
    max_tokens=1000,
)


def investigate_claim(claim_id: str):
    model_call_count = 0
    # completed_tools=set()
    tool_call_history=[]
    tool_result_history = []

    def before_model_call(event: BeforeModelCallEvent):
        nonlocal model_call_count
        model_call_count += 1
        print(f"\n========== LLM CALL #{model_call_count} ==========")
        print("\nMESSAGES SENT TO LLM:")

        for i, message in enumerate(event.agent.messages, 1):
            print(f"\n--- Message {i} ---")
            print(f"Role: {message['role']}")
            print(f"Content: {message['content']}\n")

        print(f"end of prompt")



    def after_model_call(event: AfterModelCallEvent):
        print(f"========== LLM CALL #{model_call_count} ==========\n")
        if event.stop_response:
            print(f"Stop reason: {event.stop_response.stop_reason}")
            print("Response from LLM:")
            print(event.stop_response.message)
        else:
            print("No successful model response.")

        print(f"========== END LLM CALL #{model_call_count} ==========\n")

    agent=Agent(
        model=model,
        tools=[get_claim, get_procedure,get_transaction_history, check_customer_authorization,
                validate_investigation_completeness],
    )

    def before_tool_call(event: BeforeToolCallEvent):
        tool_name=event.tool_use["name"]
        tool_input = event.tool_use["input"]

        tool_call_history.append({
            "tool": tool_name,
            "input": tool_input,
        })
        print("\n>>> TOOL CALL FROM LLM <<<")
        print(f"Tool name: {event.tool_use['name']}")
        print(f"Tool input:")
        print(event.tool_use["input"])
        print(f"Total tool calls so far: {len(tool_call_history)}")
        print(">>> END TOOL CALL <<<\n")

    def after_tool_call(event: AfterToolCallEvent):
        tool_name = event.tool_use["name"]
        tool_result = event.result

        tool_result_history.append({
            "tool": tool_name,
            "result": tool_result,
        })

        print("\n<<< TOOL RESULT <<<")
        print(f"Tool name: {tool_name}")
        print(f"Tool result:")
        print(tool_result)
        print("<<< END TOOL RESULT >>>\n")

    agent.add_hook(before_model_call)
    agent.add_hook(after_model_call)
    agent.add_hook(before_tool_call)
    agent.add_hook(after_tool_call)

    def get_tool_result(tool_name):
        for item in reversed(tool_result_history):
            if item["tool"] == tool_name:
                text = item["result"]["content"][0]["text"]
                return json.loads(text)

        return None

    # response= agent("get the details for the claim CLM001")
    # # response= agent("Investigate claim CLM002. First retrieve the claim details,"
    #                 "then retrieve the investigation procedure for its claim type.")
    # response= agent(
    #     "Investigate claim CLM002. "
    #     "Retrieve the claim details, retrieve the investigation procedure "
    #     "for its claim type, and review the recent transaction history "
    #     "before providing your investigation summary."
    # )
    # response=agent(
    #     "Investigate claim CLM002 according to the applicable "
    #     "investigation procedure and provide an investigation "
    #     "summary and recommendation."
    # )
    # response= response = agent(
    #     "Investigate claim CLM002 according to the applicable "
    #     "investigation procedure and provide an investigation "
    #     "summary. Do not make a business decision or recommend a "
    #     "refund amount. Report the investigation findings and "
    #     "customer authorization status only."
    # )

    response = agent(
        f"Investigate claim {claim_id} according to the applicable "
        "investigation procedure and provide an investigation "
        "summary. Do not make a business decision or recommend a "
        "refund amount. "
    )

    for i, call in enumerate(tool_call_history, 1):
        print(f"{i}. {call['tool']}")
        print(f"   Input: {call['input']}")

    print("========== END TOOL CALL HISTORY ==========")

    # print(response)

    claim = get_tool_result("get_claim")
    authorization = get_tool_result("check_customer_authorization")
    # procedure = get_tool_result("get_procedure")
    procedure = get_procedure(claim["claim_type"])

    completed_checks = []

    called_tools = {
        call["tool"]
        for call in tool_call_history
    }

    if "get_transaction_history" in called_tools:
        completed_checks.extend([
            "Verify ACH transaction details",
            "Check transaction originator",
            "Check customer account activity",
        ])

    if "check_customer_authorization" in called_tools:
        completed_checks.append(
            "Check whether the customer authorized the transaction"
        )
        
    validation = validate_investigation_completeness(
        procedure,
        completed_checks,
    )

    recommendation = make_recommendation(
        claim,
        authorization,
        validation,
    )

    print("\n========== FINAL BUSINESS RECOMMENDATION ==========")
    print(recommendation)

    final_result = {
        "claim_id": claim["claim_id"],
        "claim_type": claim["claim_type"],
        "customer": claim["customer"],
        "investigation_summary": str(response),
        "authorization": authorization,
        "validation": validation,
        "recommendation": recommendation,
        "tool_calls": tool_call_history,
    }

    print("\n========== FINAL INVESTIGATION RESULT ==========")
    print(json.dumps(final_result, indent=2))
    print("========== END FINAL INVESTIGATION RESULT ==========")

    return final_result


# -------------------------------------------------------------
# Allow direct execution for testing
# -------------------------------------------------------------

if __name__ == "__main__":
    investigate_claim("CLM002")