from datetime import datetime
from typing import Any


def generate_workflow(
    workflow_id: str,
    candidate: dict,
    ai_result: dict | None = None,
) -> dict:
    """
    Convert a discovered workflow candidate and optional AI understanding
    into a normalized WorkFlowOS workflow definition.

    This is the bridge between:
        Discovery / AI Understanding
    and:
        Automation Engine
    """

    ai_workflow = {}

    if ai_result:
        # Accept either:
        # {
        #   "success": True,
        #   "workflow": {...}
        # }
        #
        # or directly:
        # {
        #   "intent": "...",
        #   ...
        # }
        ai_workflow = ai_result.get("workflow", ai_result)

    # ---------------------------------------------------------
    # Basic information
    # ---------------------------------------------------------

    name = (
        ai_workflow.get("intent")
        or candidate.get("name")
        or "Automated Workflow"
    )

    summary = (
        ai_workflow.get("summary")
        or candidate.get("description")
        or "Automated repeated workflow."
    )

    # ---------------------------------------------------------
    # Trigger
    # ---------------------------------------------------------

    ai_trigger = ai_workflow.get("trigger") or {}

    trigger = {
        "type": ai_trigger.get(
            "type",
            "repeated_sequence"
        ),
        "description": ai_trigger.get(
            "description",
            f"Repeated workflow detected "
            f"{candidate.get('occurrences', 0)} time(s)."
        ),
    }

    # ---------------------------------------------------------
    # Variables
    # ---------------------------------------------------------

    variables = ai_workflow.get("variables", [])

    if not isinstance(variables, list):
        variables = []

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------

    actions = []

    ai_actions = ai_workflow.get("actions", [])

    if isinstance(ai_actions, list) and ai_actions:
        for index, action in enumerate(ai_actions, start=1):
            if not isinstance(action, dict):
                continue

            application = (
                action.get("application")
                or "Unknown Application"
            )

            description = (
                action.get("action")
                or "Perform observed action"
            )

            actions.append({
                "order": index,
                "application": application,
                "action": description,
            })

    # If AI did not produce actions, use the discovered sequence.
    if not actions:
        sequence = candidate.get("sequence", [])

        for index, step in enumerate(sequence, start=1):
            if not isinstance(step, dict):
                continue

            event_type = step.get("event_type", "")
            
            # Ignore raw application-focus events.
            if event_type == "APPLICATION_FOCUS":
                continue

            application = (
                step.get("application")
                or "Unknown Application"
            )

            target = step.get("target", "")

            action_description = _humanize_action(
                event_type,
                target
            )

            actions.append({
                "order": index,
                "application": application,
                "action": action_description,
            })

    # ---------------------------------------------------------
    # Conditions
    # ---------------------------------------------------------

    conditions = ai_workflow.get("conditions", [])

    if not isinstance(conditions, list):
        conditions = []

    normalized_conditions = []

    for condition in conditions:
        if not isinstance(condition, dict):
            continue

        normalized_conditions.append({
            "condition": condition.get(
                "condition",
                "Condition not specified"
            ),
            "otherwise": condition.get(
                "otherwise",
                "Continue workflow"
            ),
        })

    # ---------------------------------------------------------
    # Applications
    # ---------------------------------------------------------

    applications = []

    for action in actions:
        application = action["application"]

        if application not in applications:
            applications.append(application)

    # ---------------------------------------------------------
    # Final workflow
    # ---------------------------------------------------------

    workflow = {
        "workflow_id": workflow_id,
        "name": name,
        "description": summary,

        "status": "pending_approval",

        "created_at": datetime.now().isoformat(),

        "trigger": trigger,

        "variables": variables,

        "conditions": normalized_conditions,

        "actions": actions,

        "applications": applications,

        "source": {
            "occurrences": candidate.get("occurrences", 0),
            "confidence": candidate.get("confidence", 0),
            "ready_for_automation": candidate.get(
                "ready_for_automation",
                False
            ),
        },

        "execution": {
            "executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "last_run": None,
        },
    }

    return workflow


def _humanize_action(event_type: str, target: str) -> str:
    """
    Convert low-level activity events into readable workflow actions.
    """

    target_text = f" '{target}'" if target else ""

    mapping = {
        "BROWSER_NAVIGATE":
            f"Navigate to{target_text}",

        "BROWSER_INPUT":
            f"Enter data into{target_text}",

        "BROWSER_SUBMIT":
            f"Submit{target_text}",

        "CLICK":
            f"Click{target_text}",

        "INPUT":
            f"Enter data into{target_text}",

        "KEY_PRESS":
            f"Press key{target_text}",

        "FILE_OPEN":
            f"Open file{target_text}",

        "FILE_SAVE":
            f"Save file{target_text}",
    }

    return mapping.get(
        event_type,
        f"Perform {event_type or 'observed action'}{target_text}"
    )