import json
import os

from openai import OpenAI

from backend.ai.schemas import WorkflowUnderstanding


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# We use a specific free model instead of the random free router.
# Gemma 4 26B A4B supports JSON output and is available for free
# through OpenRouter.
OPENROUTER_MODEL = "google/gemma-4-26b-a4b-it:free"


def understand_with_openrouter(candidate: dict) -> WorkflowUnderstanding:

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    client = OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
    )

    prompt = f"""
You are the AI Workflow Understanding component of WorkFlowOS.

Analyze the observed computer activity and determine what the user
is trying to accomplish.

You MUST return a JSON object containing ALL of these fields:

intent
summary
trigger
variables
actions
conditions

The JSON structure must be:

{{
  "intent": "short meaningful name",
  "summary": "human-readable explanation",
  "trigger": {{
    "type": "trigger type",
    "description": "what starts the workflow"
  }},
  "variables": [],
  "actions": [
    {{
      "application": "application name",
      "action": "meaningful human-readable action"
    }}
  ],
  "conditions": [
    {{
      "condition": "condition",
      "otherwise": "what happens otherwise"
    }}
  ]
}}

IMPORTANT:

- Infer the user's intent from the observed sequence.
- Do not invent applications.
- Ignore APPLICATION_FOCUS events.
- Convert low-level browser events into meaningful actions.
- Identify values that may change between executions as variables.
- Only create conditions when the observed workflow supports them.
- ALWAYS include every field in the JSON structure.
- Return ONLY JSON. Do not include markdown.

Observed workflow candidate:

{json.dumps(candidate, indent=2)}
"""

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "OpenRouter returned an empty response."
        )

    data = json.loads(content)

    # ---------------------------------------------------------
    # Defensive normalization
    #
    # Some models may omit optional/less-important fields even
    # when instructed to provide them. Fill those fields from
    # the observed workflow rather than throwing away the AI
    # result completely.
    # ---------------------------------------------------------

    if not data.get("intent"):
        data["intent"] = candidate.get(
            "name",
            "Automate Repeated Workflow"
        )

    if not data.get("summary"):
        data["summary"] = candidate.get(
            "description",
            "Automate a repeated sequence of user actions."
        )

    if not data.get("trigger"):
        occurrences = candidate.get("occurrences", 0)

        data["trigger"] = {
            "type": "repeated_sequence",
            "description": (
                f"Repeated workflow detected "
                f"{occurrences} time(s)."
            )
        }

    if not isinstance(data.get("variables"), list):
        data["variables"] = []

    if not isinstance(data.get("actions"), list):
        data["actions"] = []

    if not isinstance(data.get("conditions"), list):
        data["conditions"] = []

    # Make sure the trigger itself is a dictionary.
    if not isinstance(data.get("trigger"), dict):
        data["trigger"] = {
            "type": "repeated_sequence",
            "description": "Repeated workflow detected."
        }

    return WorkflowUnderstanding.model_validate(data)