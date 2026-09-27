"""
WorkFlowOS Recommendation Engine

Converts discovered workflow candidates into
user-facing automation recommendations.

This version is intentionally deterministic so
the hackathon prototype can run completely locally.
"""

from typing import Any, Dict, List


# ============================================================
# CONFIGURATION
# ============================================================

MIN_OCCURRENCES = 3

MIN_CONFIDENCE = 0.70


# ============================================================
# SINGLE RECOMMENDATION
# ============================================================

def generate_recommendation(
    candidate: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert one workflow-discovery candidate into
    a user-facing automation recommendation.
    """

    occurrences = int(
        candidate.get(
            "occurrences",
            0
        )
    )

    confidence = float(
        candidate.get(
            "confidence",
            0
        )
    )

    workflow_id = candidate.get(
        "workflow_id"
    )

    name = candidate.get(
        "name",
        "Repeated Workflow"
    )

    description = candidate.get(
        "description",
        "A repeated workflow was detected."
    )

    applications = candidate.get(
        "applications",
        []
    )

    sequence = candidate.get(
        "sequence",
        []
    )


    # --------------------------------------------------------
    # SHOULD WE RECOMMEND IT?
    # --------------------------------------------------------

    should_recommend = (
        occurrences >= MIN_OCCURRENCES
        and
        confidence >= MIN_CONFIDENCE
    )


    # --------------------------------------------------------
    # CONVERT INTERNAL STEPS INTO READABLE STEPS
    # --------------------------------------------------------

    readable_steps = []

    for item in sequence:

        application = item.get(
            "application",
            ""
        )

        event_type = item.get(
            "event_type",
            ""
        )

        target = item.get(
            "target",
            ""
        )


        if event_type == "BROWSER_NAVIGATE":

            action = (
                f"Open {application}"
            )

        elif event_type == "BROWSER_INPUT":

            if target:

                action = (
                    f"Enter information into "
                    f"{target}"
                )

            else:

                action = (
                    f"Enter information in "
                    f"{application}"
                )

        elif event_type == "BROWSER_SUBMIT":

            if target:

                action = (
                    f"Submit {target}"
                )

            else:

                action = (
                    f"Submit form in "
                    f"{application}"
                )

        else:

            action = (
                f"Perform {event_type}"
            )


        readable_steps.append({

            "application":
                application,

            "event_type":
                event_type,

            "target":
                target,

            "action":
                action
        })


    # --------------------------------------------------------
    # USER-FACING MESSAGE
    # --------------------------------------------------------

    message = (
        f"You have performed "
        f"'{name}' "
        f"{occurrences} times. "
        f"Would you like to automate it?"
    )


    # --------------------------------------------------------
    # RECOMMENDATION OBJECT
    # --------------------------------------------------------

    return {

        "workflow_id":
            workflow_id,

        "type":
            "AUTOMATION_OPPORTUNITY",

        "title":
            f"Automate: {name}",

        "message":
            message,

        "description":
            description,

        "occurrences":
            occurrences,

        "confidence":
            confidence,

        "applications":
            applications,

        "steps":
            readable_steps,

        "should_recommend":
            should_recommend,

        "available_actions": [

            {
                "id":
                    "approve",

                "label":
                    "Automate",

                "action":
                    "CREATE_AUTOMATION"
            },

            {
                "id":
                    "dismiss",

                "label":
                    "Dismiss",

                "action":
                    "DISMISS_RECOMMENDATION"
            }

        ]
    }


# ============================================================
# ALL RECOMMENDATIONS
# ============================================================

def generate_recommendations(
    candidates: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Convert all discovered workflow candidates
    into recommendations.
    """

    recommendations = []

    for candidate in candidates:

        recommendation = (
            generate_recommendation(
                candidate
            )
        )

        if recommendation[
            "should_recommend"
        ]:

            recommendations.append(
                recommendation
            )


    return recommendations