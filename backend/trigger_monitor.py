import json
import threading
import time

from backend.workflow_store import get_all_workflows


CHECK_INTERVAL = 1.0


class TriggerMonitor:

    def __init__(self):

        self.running = False
        self.thread = None

        # Events that existed before the monitor started
        # should not trigger workflows.
        self.last_event_id = 0

    def start(self):

        if self.running:
            return

        try:

            from backend.database import get_events

            existing_events = get_events(limit=1)

            if existing_events:

                self.last_event_id = int(
                    existing_events[0].get("id", 0)
                )

        except Exception as error:

            print(
                f"[TRIGGER] Could not initialize "
                f"event position: {error}"
            )

        self.running = True

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )

        self.thread.start()

        print(
            "[TRIGGER] Trigger monitor started."
        )

    def stop(self):

        self.running = False

        if self.thread:

            self.thread.join(
                timeout=2
            )

        print(
            "[TRIGGER] Trigger monitor stopped."
        )

    def _run(self):

        while self.running:

            try:

                self._check_for_triggers()

            except Exception as error:

                print(
                    f"[TRIGGER] Monitor error: {error}"
                )

            time.sleep(
                CHECK_INTERVAL
            )

    def _check_for_triggers(self):

        from backend.database import get_events

        events = get_events(
            limit=100
        )

        if not events:
            return

        # Database normally returns newest first.
        # Process oldest → newest.
        events = list(
            reversed(events)
        )

        for event in events:

            try:

                event_id = int(
                    event.get("id", 0)
                )

            except (TypeError, ValueError):

                continue

            if event_id <= self.last_event_id:
                continue

            self.last_event_id = event_id

            print(
                f"[TRIGGER] New event detected: "
                f"{event.get('event_type', event.get('type', 'UNKNOWN'))}"
            )

            self._process_event(
                event
            )

    def _process_event(self, event):

        workflows = get_all_workflows()

        for workflow in workflows:

            status = workflow.get(
                "status"
            )

            if status != "active":
                continue

            print(
                f"[TRIGGER] Checking active workflow: "
                f"{workflow.get('name')}"
            )

            if self._matches_trigger(
                workflow,
                event
            ):

                print()
                print(
                    "=" * 70
                )
                print(
                    "[TRIGGER] WORKFLOW TRIGGERED"
                )
                print(
                    f"[TRIGGER] "
                    f"{workflow.get('name')}"
                )
                print(
                    "=" * 70
                )

                self._execute_workflow(
                    workflow,
                    event
                )

    def _get_metadata(self, event):

        metadata = event.get(
            "metadata",
            {}
        )

        if isinstance(
            metadata,
            dict
        ):

            return metadata

        if isinstance(
            metadata,
            str
        ):

            try:

                return json.loads(
                    metadata
                )

            except json.JSONDecodeError:

                return {}

        return {}

    def _matches_trigger(
        self,
        workflow,
        event
    ):

        metadata = self._get_metadata(
            event
        )

        # -------------------------------------------------
        # Event information
        # -------------------------------------------------

        event_type = str(
            event.get(
                "event_type",
                event.get("type", "")
            )
        ).upper()

        application = str(
            event.get(
                "application",
                ""
            )
        ).lower()

        # target may be stored directly
        # or inside metadata.
        target = str(
            event.get(
                "target",
                metadata.get(
                    "target",
                    ""
                )
            )
        ).lower()

        trigger = workflow.get(
            "trigger",
            {}
        )

        trigger_type = str(
            trigger.get(
                "type",
                ""
            )
        ).lower()

        trigger_description = str(
            trigger.get(
                "description",
                ""
            )
        ).lower()

        print(
            f"[TRIGGER]   Event: {event_type}"
        )

        print(
            f"[TRIGGER]   Application: "
            f"{application}"
        )

        print(
            f"[TRIGGER]   Target: {target}"
        )

        print(
            f"[TRIGGER]   Trigger type: "
            f"{trigger_type}"
        )

        # -------------------------------------------------
        # PRIMARY CUSTOMER PORTAL TRIGGER
        # -------------------------------------------------

        if event_type == "BROWSER_SUBMIT":

            is_customer_portal = (
                "customer portal"
                in application
            )

            is_customer_request = (
                "customer_request"
                in target
                or "customer request"
                in target
            )

            if (
                is_customer_portal
                and is_customer_request
            ):

                print(
                    "[TRIGGER]   ✓ Customer request "
                    "submission matched."
                )

                return True

        # -------------------------------------------------
        # Generic form trigger fallback
        # -------------------------------------------------

        if event_type == "BROWSER_SUBMIT":

            if (
                "customer request"
                in trigger_description
                or "form"
                in trigger_description
                or "submit"
                in trigger_description
            ):

                print(
                    "[TRIGGER]   ✓ Generic form "
                    "trigger matched."
                )

                return True

        return False

    def _execute_workflow(
        self,
        workflow,
        event
    ):

        try:

            from backend.automation_engine import (
                execute_workflow
            )

            result = execute_workflow(
                workflow,
                trigger_event=event
            )

            print(
                "[TRIGGER] Execution result:",
                result.get("status")
            )

        except Exception as error:

            print(
                f"[TRIGGER] Automation error: "
                f"{error}"
            )


trigger_monitor = TriggerMonitor()