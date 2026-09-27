"""
WorkFlowOS Workflow Discovery Engine

Detects repeated workflows from semantic browser activity.

Current demo workflow:

Customer Portal
    -> submit customer request
    -> Customer CRM
    -> update customer
    -> Team Notifications
    -> send notification

The detector deliberately ignores the actual values entered by
the user. It compares the structure of the activity instead.
"""

import json
from collections import Counter
from datetime import datetime, timezone


# ============================================================
# CONFIGURATION
# ============================================================

MIN_WORKFLOW_OCCURRENCES = 3

SESSION_GAP_SECONDS = 300

MAX_SEQUENCE_LENGTH = 50


# ============================================================
# APPLICATION DEFINITIONS
# ============================================================

CUSTOMER_PORTAL = "Customer Portal"

CUSTOMER_CRM = "Customer CRM"

TEAM_NOTIFICATIONS = "Team Notifications"


# ============================================================
# METADATA
# ============================================================

def parse_metadata(metadata):

    if not metadata:
        return {}

    if isinstance(metadata, dict):
        return metadata

    if isinstance(metadata, str):

        try:

            result = json.loads(metadata)

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

    return {}


# ============================================================
# TIMESTAMP
# ============================================================

def parse_timestamp(timestamp):

    if not timestamp:
        return None

    try:

        normalized = timestamp.replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            normalized
        )

        # Windows agent timestamps may be
        # timezone-naive.
        if dt.tzinfo is None:

            dt = dt.astimezone()

        return dt.astimezone(
            timezone.utc
        )

    except (
        ValueError,
        TypeError,
        AttributeError
    ):

        return None


# ============================================================
# NORMALIZE EVENT
# ============================================================

def normalize_event(event):

    metadata = parse_metadata(
        event.get("metadata")
    )

    return {

        "id":
            event.get("id"),

        "timestamp":
            event.get("timestamp"),

        "datetime":
            parse_timestamp(
                event.get("timestamp")
            ),

        "application":
            event.get("application") or "",

        "event_type":
            event.get("event_type") or "",

        "window_title":
            event.get("window_title") or "",

        "target":
            metadata.get("target") or "",

        "url":
            metadata.get("url") or "",

        "metadata":
            metadata
    }


# ============================================================
# NORMALIZE ALL EVENTS
# ============================================================

def normalize_events(events):

    normalized = [
        normalize_event(event)
        for event in events
    ]

    # Oldest -> newest
    normalized.sort(
        key=lambda event: (
            event["datetime"] is None,
            event["datetime"]
            or datetime.max.replace(
                tzinfo=timezone.utc
            )
        )
    )

    return normalized


# ============================================================
# BUILD SESSIONS
# ============================================================

def build_sessions(events):

    normalized = normalize_events(
        events
    )

    if not normalized:
        return []

    sessions = []

    current_session = []

    previous_time = None

    for event in normalized:

        current_time = event["datetime"]

        if (
            previous_time is not None
            and current_time is not None
        ):

            gap = (
                current_time
                - previous_time
            ).total_seconds()

            if gap > SESSION_GAP_SECONDS:

                if current_session:

                    sessions.append(
                        current_session
                    )

                current_session = []

        current_session.append(event)

        if current_time is not None:

            previous_time = current_time

    if current_session:

        sessions.append(
            current_session
        )

    return sessions


# ============================================================
# EVENT SIGNATURE
# ============================================================

def event_signature(event):

    return (
        event["application"],
        event["event_type"],
        event["target"]
    )


# ============================================================
# WORKFLOW RUN DETECTION
# ============================================================

def extract_workflow_runs(session):
    """
    Detect complete workflow runs.

    IMPORTANT:

    A workflow run begins with a Customer Portal
    BROWSER_SUBMIT event.

    We do NOT require BROWSER_NAVIGATE.

    This allows the user to perform the workflow multiple
    times without refreshing the browser page.
    """

    runs = []

    current_run = None

    stage = None


    for event in session:

        application = event["application"]

        event_type = event["event_type"]


        # ====================================================
        # CUSTOMER PORTAL SUBMISSION
        # ====================================================

        if (
            application == CUSTOMER_PORTAL
            and event_type == "BROWSER_SUBMIT"
        ):

            # Start a brand-new workflow run.

            current_run = [event]

            stage = "customer_portal"

            continue


        # ====================================================
        # IGNORE EVENTS BEFORE FIRST SUBMISSION
        # ====================================================

        if current_run is None:

            continue


        # Add events belonging to current run.

        current_run.append(event)


        # ====================================================
        # CUSTOMER CRM SUBMISSION
        # ====================================================

        if (
            application == CUSTOMER_CRM
            and event_type == "BROWSER_SUBMIT"
        ):

            stage = "customer_crm"

            continue


        # ====================================================
        # TEAM NOTIFICATION SUBMISSION
        # ====================================================

        if (
            application == TEAM_NOTIFICATIONS
            and event_type == "BROWSER_SUBMIT"
        ):

            # Complete workflow found.

            runs.append(
                current_run
            )

            current_run = None

            stage = None


    return runs


# ============================================================
# CREATE STRUCTURAL SEQUENCE
# ============================================================

def extract_sequence(workflow_run):

    sequence = []

    for event in workflow_run:

        signature = event_signature(
            event
        )

        # Remove consecutive duplicates.

        if (
            not sequence
            or sequence[-1] != signature
        ):

            sequence.append(
                signature
            )

    return sequence[
        :MAX_SEQUENCE_LENGTH
    ]


# ============================================================
# HUMAN-READABLE STEPS
# ============================================================

def sequence_to_steps(sequence):

    steps = []

    for index, item in enumerate(
        sequence,
        start=1
    ):

        steps.append({

            "step":
                index,

            "application":
                item[0],

            "event_type":
                item[1],

            "target":
                item[2]
        })

    return steps


# ============================================================
# WORKFLOW SUMMARY
# ============================================================

def create_workflow_summary(sequence):

    applications = []

    for item in sequence:

        application = item[0]

        if application not in applications:

            applications.append(
                application
            )


    if (
        CUSTOMER_PORTAL in applications
        and CUSTOMER_CRM in applications
        and TEAM_NOTIFICATIONS in applications
    ):

        return {

            "name":
                "Process Customer Request",

            "description":
                (
                    "Collect a customer request, "
                    "update the customer CRM record, "
                    "and notify the team."
                ),

            "applications":
                applications
        }


    return {

        "name":
            "Repeated Workflow",

        "description":
            (
                "A repeated sequence of "
                "user actions was detected."
            ),

        "applications":
            applications
    }


# ============================================================
# MAIN DISCOVERY FUNCTION
# ============================================================

def find_repeated_workflows(events):

    if not events:

        return []


    # --------------------------------------------------------
    # STEP 1: BUILD SESSIONS
    # --------------------------------------------------------

    sessions = build_sessions(
        events
    )


    # --------------------------------------------------------
    # STEP 2: FIND COMPLETE WORKFLOW RUNS
    # --------------------------------------------------------

    workflow_runs = []


    for session in sessions:

        runs = extract_workflow_runs(
            session
        )

        workflow_runs.extend(
            runs
        )


    if not workflow_runs:

        return []


    # --------------------------------------------------------
    # STEP 3: CREATE STRUCTURAL SEQUENCES
    # --------------------------------------------------------

    sequences = []


    for run in workflow_runs:

        sequence = extract_sequence(
            run
        )

        if sequence:

            sequences.append(
                sequence
            )


    # --------------------------------------------------------
    # STEP 4: COUNT IDENTICAL PATTERNS
    # --------------------------------------------------------

    sequence_counts = Counter(
        tuple(sequence)
        for sequence in sequences
    )


    candidates = []


    # --------------------------------------------------------
    # STEP 5: CREATE WORKFLOW CANDIDATES
    # --------------------------------------------------------

    for sequence_tuple, count in (
        sequence_counts.items()
    ):

        if count < MIN_WORKFLOW_OCCURRENCES:

            continue


        sequence = list(
            sequence_tuple
        )


        # Confidence based on repetitions.

        if count == 3:

            confidence = 0.80

        elif count == 4:

            confidence = 0.90

        else:

            confidence = 0.95


        summary = create_workflow_summary(
            sequence
        )


        candidates.append({

            "workflow_id":
                f"workflow_{len(candidates) + 1}",

            "name":
                summary["name"],

            "description":
                summary["description"],

            "applications":
                summary["applications"],

            "sequence":
                sequence_to_steps(
                    sequence
                ),

            "occurrences":
                count,

            "confidence":
                confidence,

            "ready_for_automation":
                True
        })


    # Highest repetition first.

    candidates.sort(
        key=lambda candidate:
            candidate["occurrences"],
        reverse=True
    )


    return candidates


# ============================================================
# DEBUG INFORMATION
# ============================================================

def get_discovery_debug_info(events):

    sessions = build_sessions(
        events
    )


    workflow_runs = []


    for session in sessions:

        workflow_runs.extend(
            extract_workflow_runs(
                session
            )
        )


    return {

        "total_events":
            len(events),

        "sessions":
            len(sessions),

        "workflow_runs":
            len(workflow_runs),

        "minimum_occurrences_required":
            MIN_WORKFLOW_OCCURRENCES
    }