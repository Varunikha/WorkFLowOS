import json

import ollama

from backend.ai.schemas import WorkflowUnderstanding


OLLAMA_MODEL = "qwen3:4b"


def understand_with_ollama(candidate: dict) -> WorkflowUnderstanding:

    prompt = f"""
You are the AI Workflow Understanding component of WorkFlowOS.

WorkFlowOS observes a user's computer activity and detects repeated sequences
of actions. Your job is to understand what the user is trying to accomplish.

Analyze the observed workflow below.

IMPORTANT:
- Infer the user's overall intent from the sequence.
- Do not invent applications that are not present.
- Do not assume that every workflow is a customer-support workflow.
- Keep application names and actions grounded in the observed data.
- Identify variables that may change between executions.
- Identify useful conditions only when supported by the workflow.
- Return ONLY the requested structured output.

Observed workflow candidate:

{json.dumps(candidate, indent=2)}
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format=WorkflowUnderstanding.model_json_schema(),
        options={
            "temperature": 0
        }
    )

    content = response["message"]["content"]

    data = json.loads(content)

    return WorkflowUnderstanding.model_validate(data)