import json
import os
from datetime import datetime


WORKFLOW_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "generated_workflows.json",
)


def _ensure_storage():
    os.makedirs(
        os.path.dirname(WORKFLOW_FILE),
        exist_ok=True,
    )

    if not os.path.exists(WORKFLOW_FILE):
        with open(
            WORKFLOW_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump({}, file, indent=2)


def _load_workflows():
    _ensure_storage()

    try:
        with open(
            WORKFLOW_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}


def _save_workflows(workflows):
    _ensure_storage()

    with open(
        WORKFLOW_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            workflows,
            file,
            indent=2,
        )


def save_workflow(workflow: dict) -> dict:
    workflows = _load_workflows()

    workflow_id = workflow["workflow_id"]

    workflows[workflow_id] = workflow

    _save_workflows(workflows)

    return workflow


def get_workflow(workflow_id: str):
    workflows = _load_workflows()

    return workflows.get(workflow_id)


def get_all_workflows():
    workflows = _load_workflows()

    return list(workflows.values())


def update_workflow_status(
    workflow_id: str,
    status: str,
):
    workflows = _load_workflows()

    workflow = workflows.get(workflow_id)

    if workflow is None:
        return None

    workflow["status"] = status

    workflow.setdefault(
        "lifecycle",
        {},
    )

    if status == "active":

        workflow["lifecycle"]["approved_at"] = (
            datetime.now().isoformat()
        )

        workflow["lifecycle"]["enabled"] = True

    elif status in (
        "disabled",
        "dismissed",
    ):

        workflow["lifecycle"]["enabled"] = False

    _save_workflows(workflows)

    return workflow