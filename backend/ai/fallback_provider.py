from backend.ai.schemas import (
    WorkflowAction,
    WorkflowCondition,
    WorkflowTrigger,
    WorkflowUnderstanding,
)


def _extract_steps(candidate: dict) -> list:
    """
    Try to retrieve workflow steps from the candidate regardless
    of the exact representation used by the discovery engine.
    """

    possible_keys = [
        "sequence",
        "steps",
        "events",
        "workflow",
    ]

    for key in possible_keys:
        value = candidate.get(key)

        if isinstance(value, list):
            return value

    return []


def _describe_step(step: dict) -> tuple[str, str]:

    application = (
        step.get("application")
        or step.get("app")
        or step.get("application_name")
        or "Unknown Application"
    )

    action = (
        step.get("action")
        or step.get("event_type")
        or step.get("type")
        or "Perform observed action"
    )

    return str(application), str(action)


def understand_with_fallback(candidate: dict) -> WorkflowUnderstanding:

    steps = _extract_steps(candidate)

    actions = []

    applications = []

    for step in steps:

        if not isinstance(step, dict):
            continue

        application, action = _describe_step(step)

        actions.append(
            WorkflowAction(
                application=application,
                action=action
            )
        )

        if application not in applications:
            applications.append(application)

    if applications:
        intent = "Automate Repeated Workflow"

        summary = (
            "Automate a repeated sequence of actions across "
            + ", ".join(applications)
            + "."
        )

    else:
        intent = "Automate Repeated Activity"

        summary = (
            "Automate a repeated sequence of observed user activity."
        )

    occurrences = candidate.get("occurrences", 0)

    trigger = WorkflowTrigger(
        type="repeated_sequence",
        description=(
            f"Repeated workflow detected {occurrences} time(s)."
        )
    )

    return WorkflowUnderstanding(
        intent=intent,
        summary=summary,
        trigger=trigger,
        variables=[],
        actions=actions,
        conditions=[]
    )