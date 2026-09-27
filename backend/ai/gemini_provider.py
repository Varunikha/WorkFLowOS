import json
import os

from google import genai

from backend.ai.schemas import WorkflowUnderstanding


GEMINI_MODEL = "gemini-3.8-flash"


def understand_with_gemini(candidate: dict) -> WorkflowUnderstanding:

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=api_key
    )

    prompt = f"""
You are the AI Workflow Understanding component of WorkFlowOS.

WorkFlowOS observes a user's computer activity and detects repeated sequences
of actions.

Your task is to infer what the user is trying to accomplish from the observed
workflow.

IMPORTANT RULES:

1. Infer the user's overall intent from the observed sequence.
2. Do not invent applications that are not present.
3. Ignore low-level APPLICATION_FOCUS events when they do not represent
   meaningful user actions.
4. Convert low-level browser actions into meaningful human-readable actions.
5. Identify important variables that may change between executions.
6. Identify conditions only when supported by the observed workflow.
7. Return only the structured workflow.

Observed workflow candidate:

{json.dumps(candidate, indent=2)}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": WorkflowUnderstanding,
        },
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    data = json.loads(response.text)

    return WorkflowUnderstanding.model_validate(data)