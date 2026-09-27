import json
from datetime import datetime

from playwright.sync_api import sync_playwright

from backend.workflow_store import save_workflow


# ============================================================
# REAL DEMO APPLICATION URLS
# ============================================================

CUSTOMER_CRM_URL = "http://localhost:3000/crm/"
TEAM_NOTIFICATIONS_URL = "http://localhost:3000/notifications/"


# ============================================================
# TRIGGER DATA
# ============================================================

def _get_trigger_metadata(trigger_event):
    """
    Extract metadata from the event that triggered the workflow.

    SQLite may return metadata as either:
        - a Python dictionary
        - a JSON string
    """

    if not trigger_event:
        return {}

    metadata = trigger_event.get("metadata", {})

    if isinstance(metadata, dict):
        return metadata

    if isinstance(metadata, str):

        try:
            return json.loads(metadata)

        except json.JSONDecodeError:
            return {}

    return {}


# ============================================================
# MAIN WORKFLOW EXECUTION
# ============================================================

def execute_workflow(workflow, trigger_event=None):

    workflow_id = workflow["workflow_id"]

    started_at = datetime.now()

    executed_actions = []

    # --------------------------------------------------------
    # Extract information from the triggering Customer Portal
    # event.
    # --------------------------------------------------------

    metadata = _get_trigger_metadata(trigger_event)

    customer = metadata.get(
        "customer",
        ""
    )

    email = metadata.get(
        "email",
        ""
    )

    request = metadata.get(
        "request",
        ""
    )

    request_id = metadata.get(
        "request_id",
        ""
    )

    print()
    print("=" * 70)
    print("[AUTOMATION] APPROVED WORKFLOW EXECUTION STARTED")
    print("=" * 70)

    print(
        f"[AUTOMATION] Workflow: "
        f"{workflow.get('name')}"
    )

    print(
        f"[AUTOMATION] Customer: "
        f"{customer}"
    )

    print(
        f"[AUTOMATION] Email: "
        f"{email}"
    )

    print(
        f"[AUTOMATION] Request ID: "
        f"{request_id}"
    )

    # --------------------------------------------------------
    # Validate trigger data
    # --------------------------------------------------------

    if not customer or not request:

        error = (
            "The trigger event does not contain "
            "customer and request information."
        )

        print(
            f"[AUTOMATION] ERROR: {error}"
        )

        return _record_failure(
            workflow=workflow,
            workflow_id=workflow_id,
            error=error,
            executed_actions=executed_actions,
            started_at=started_at,
        )

    try:

        # ====================================================
        # START PLAYWRIGHT
        # ====================================================

        with sync_playwright() as playwright:

            browser = playwright.chromium.launch(
                headless=False,
                slow_mo=400,
            )

            context = browser.new_context(
                viewport={
                    "width": 1400,
                    "height": 900,
                }
            )

            # =================================================
            # ACTION 1
            # CUSTOMER CRM
            # =================================================

            print()
            print(
                "[AUTOMATION] STEP 1/2"
            )

            print(
                "[AUTOMATION] Opening Customer CRM..."
            )

            crm_page = context.new_page()

            crm_page.goto(
                CUSTOMER_CRM_URL,
                wait_until="domcontentloaded",
            )

            crm_page.bring_to_front()

            # Actual selector from your CRM.
            crm_page.wait_for_selector(
                "#customerName"
            )

            crm_page.wait_for_selector(
                "#request"
            )

            print(
                "[AUTOMATION] Filling customer name..."
            )

            crm_page.locator(
                "#customerName"
            ).fill(customer)

            print(
                "[AUTOMATION] Filling customer request..."
            )

            crm_page.locator(
                "#request"
            ).fill(request)

            print(
                "[AUTOMATION] Submitting CRM update..."
            )

            # Your CRM uses:
            # <form id="crmForm">
            #
            # Submitting the form is more robust than relying
            # on a button ID because the actual button currently
            # does not have an ID.

            crm_page.locator(
                "#crmForm"
            ).evaluate(
                "(form) => form.requestSubmit()"
            )

            # Your CRM displays #result after submission.
            crm_page.wait_for_selector(
                "#result",
                state="visible",
            )

            crm_page.wait_for_timeout(
                800
            )

            crm_result = (
                crm_page
                .locator("#result")
                .inner_text()
            )

            print(
                "[AUTOMATION] CRM result:"
            )

            print(
                crm_result
            )

            executed_actions.append({
                "order": 1,
                "application": "Customer CRM",
                "action": "Update customer record",
                "status": "success",
            })

            # =================================================
            # ACTION 2
            # TEAM NOTIFICATIONS
            # =================================================

            print()
            print(
                "[AUTOMATION] STEP 2/2"
            )

            print(
                "[AUTOMATION] Opening Team Notifications..."
            )

            notification_page = (
                context.new_page()
            )

            notification_page.goto(
                TEAM_NOTIFICATIONS_URL,
                wait_until="domcontentloaded",
            )

            notification_page.bring_to_front()

            # These selectors correspond to the
            # notification demo we created earlier.
            notification_page.wait_for_selector(
                "#message"
            )

            notification_message = (
                "New customer request received.\n\n"
                f"Customer: {customer}\n"
                f"Email: {email}\n"
                f"Request ID: {request_id}\n\n"
                f"Request:\n{request}"
            )

            print(
                "[AUTOMATION] Creating team notification..."
            )

            notification_page.locator(
                "#message"
            ).fill(
                notification_message
            )

            print(
                "[AUTOMATION] Sending team notification..."
            )

            notification_page.locator(
                "#sendButton"
            ).click()

            notification_page.wait_for_selector(
                "#status",
                state="visible",
            )

            notification_page.wait_for_timeout(
                800
            )

            notification_result = (
                notification_page
                .locator("#status")
                .inner_text()
            )

            print(
                "[AUTOMATION] Notification result:"
            )

            print(
                notification_result
            )

            executed_actions.append({
                "order": 2,
                "application": "Team Notifications",
                "action": "Send team notification",
                "status": "success",
            })

            # =================================================
            # WORKFLOW COMPLETE
            # =================================================

            print()
            print("=" * 70)
            print(
                "[AUTOMATION] WORKFLOW COMPLETED SUCCESSFULLY"
            )
            print("=" * 70)

            # Keep the browser visible briefly so the demo
            # clearly shows the completed automation.

            notification_page.wait_for_timeout(
                3000
            )

            browser.close()

        # ====================================================
        # RECORD SUCCESS
        # ====================================================

        finished_at = datetime.now()

        duration = (
            finished_at - started_at
        ).total_seconds()

        workflow.setdefault(
            "execution",
            {}
        )

        workflow["execution"]["executions"] = (
            workflow["execution"].get(
                "executions",
                0
            ) + 1
        )

        workflow["execution"]["successful_executions"] = (
            workflow["execution"].get(
                "successful_executions",
                0
            ) + 1
        )

        workflow["execution"]["last_run"] = (
            finished_at.isoformat()
        )

        save_workflow(
            workflow
        )

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": duration,
            "trigger_event": trigger_event,
            "actions": executed_actions,
        }

    except Exception as error:

        print()
        print("=" * 70)
        print(
            "[AUTOMATION] WORKFLOW EXECUTION FAILED"
        )
        print(
            f"[AUTOMATION] {error}"
        )
        print("=" * 70)

        return _record_failure(
            workflow=workflow,
            workflow_id=workflow_id,
            error=str(error),
            executed_actions=executed_actions,
            started_at=started_at,
        )


# ============================================================
# FAILURE RECORDING
# ============================================================

def _record_failure(
    workflow,
    workflow_id,
    error,
    executed_actions,
    started_at,
):

    finished_at = datetime.now()

    workflow.setdefault(
        "execution",
        {}
    )

    workflow["execution"]["executions"] = (
        workflow["execution"].get(
            "executions",
            0
        ) + 1
    )

    workflow["execution"]["failed_executions"] = (
        workflow["execution"].get(
            "failed_executions",
            0
        ) + 1
    )

    workflow["execution"]["last_run"] = (
        finished_at.isoformat()
    )

    save_workflow(
        workflow
    )

    return {
        "status": "failed",
        "workflow_id": workflow_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "error": error,
        "actions": executed_actions,
    }