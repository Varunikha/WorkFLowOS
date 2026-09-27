import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import (
    initialize_database,
    insert_event,
    get_events as db_get_events,
    clear_events as db_clear_events,
)

from backend.discovery import find_repeated_workflows

from backend.recommendation import generate_recommendations

from backend.ai import understand_workflow

from backend.workflow_generator import generate_workflow

from backend.workflow_store import (
    save_workflow,
    get_workflow,
    get_all_workflows,
    update_workflow_status,
)

from backend.trigger_monitor import trigger_monitor


# ============================================================
# WorkFlowOS Backend
# ============================================================

app = FastAPI(
    title="WorkFlowOS API",
    description="Backend for the WorkFlowOS activity and workflow engine",
    version="0.2.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        # Demo applications
        "http://localhost:3000",
        "http://127.0.0.1:3000",

        # WorkFlowOS frontend
        "http://localhost:3001",
        "http://127.0.0.1:3001",

        # Other possible frontend ports
        "http://localhost:3002",
        "http://127.0.0.1:3002",

        "http://localhost:3003",
        "http://127.0.0.1:3003",

        # Vite development server
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATA MODEL
# ============================================================

class ActivityEvent(BaseModel):
    timestamp: str
    application: str
    event_type: str
    window_title: str = ""
    metadata: dict = {}


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    initialize_database()

    print("WorkFlowOS database initialized.")

    # Start the workflow trigger monitor
    trigger_monitor.start()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "WorkFlowOS",
        "status": "running",
        "version": "0.2.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# RECEIVE ACTIVITY EVENT
# ============================================================

@app.post("/events")
def receive_event(event: ActivityEvent):

    event_id = insert_event(
        timestamp=event.timestamp,
        application=event.application,
        event_type=event.event_type,
        window_title=event.window_title,
        metadata=json.dumps(event.metadata),
    )

    return {
        "success": True,
        "event_id": event_id,
    }


# ============================================================
# GET ACTIVITY EVENTS
# ============================================================

@app.get("/events")
def get_events():

    events = db_get_events()

    return {
        "events": events
    }


# ============================================================
# CLEAR ACTIVITY EVENTS
# ============================================================

@app.delete("/events")
def clear_events():

    db_clear_events()

    return {
        "success": True,
        "message": "Activity history cleared",
    }


# ============================================================
# WORKFLOW DISCOVERY
# ============================================================

@app.get("/discover")
def discover_workflows():

    events = db_get_events(
        limit=5000
    )

    candidates = find_repeated_workflows(
        events
    )

    return {
        "workflow_candidates": candidates
    }


# ============================================================
# AUTOMATION RECOMMENDATIONS
# ============================================================

@app.get("/recommendations")
def get_recommendations():

    events = db_get_events(
        limit=5000
    )

    candidates = find_repeated_workflows(
        events
    )

    recommendations = generate_recommendations(
        candidates
    )

    return {
        "recommendations": recommendations,
        "count": len(recommendations)
    }


# ============================================================
# AI WORKFLOW UNDERSTANDING
# ============================================================

@app.post("/ai/understand/{workflow_id}")
def ai_understand_workflow(workflow_id: str):

    events = db_get_events(
        limit=5000
    )

    candidates = find_repeated_workflows(
        events
    )

    candidate = None

    for item in candidates:

        if item.get("workflow_id") == workflow_id:

            candidate = item
            break

    if candidate is None:

        return {
            "success": False,
            "error": "Workflow candidate not found."
        }

    result = understand_workflow(
        candidate
    )

    return {
        "workflow_id": workflow_id,
        "candidate": candidate,
        "ai": result
    }


# ============================================================
# WORKFLOW GENERATION
# ============================================================

@app.post("/workflows/generate/{workflow_id}")
def generate_workflow_endpoint(workflow_id: str):
    """
    Generate a normalized executable workflow from a
    discovered workflow candidate.

    AI understanding is attempted first.
    If AI is unavailable, the workflow generator can
    still produce a deterministic workflow.
    """

    events = db_get_events(
        limit=5000
    )

    candidates = find_repeated_workflows(
        events
    )

    candidate = None

    for item in candidates:

        if item.get("workflow_id") == workflow_id:

            candidate = item
            break

    if candidate is None:

        return {
            "success": False,
            "error": "Workflow candidate not found."
        }

    # AI understanding
    ai_result = understand_workflow(
        candidate
    )

    # Generate normalized executable workflow
    workflow = generate_workflow(
        workflow_id=workflow_id,
        candidate=candidate,
        ai_result=ai_result.get("workflow")
    )

    # Persist workflow
    save_workflow(workflow)

    return {
        "success": True,
        "workflow": workflow,
        "ai": ai_result,
    }


# ============================================================
# APPROVE WORKFLOW
# ============================================================

@app.post("/workflows/{workflow_id}/approve")
def approve_workflow(workflow_id: str):

    workflow = update_workflow_status(
        workflow_id,
        "active",
    )

    if workflow is None:

        return {
            "success": False,
            "error": "Workflow not found.",
        }

    return {
        "success": True,
        "message": "Workflow approved and activated.",
        "workflow": workflow,
    }


# ============================================================
# DISMISS WORKFLOW
# ============================================================

@app.post("/workflows/{workflow_id}/dismiss")
def dismiss_workflow(workflow_id: str):

    workflow = update_workflow_status(
        workflow_id,
        "dismissed",
    )

    if workflow is None:

        return {
            "success": False,
            "error": "Workflow not found.",
        }

    return {
        "success": True,
        "message": "Workflow dismissed.",
        "workflow": workflow,
    }


# ============================================================
# LIST WORKFLOWS
# ============================================================

@app.get("/workflows")
def list_workflows():

    return {
        "success": True,
        "workflows": get_all_workflows(),
    }


# ============================================================
# GET SINGLE WORKFLOW
# ============================================================

@app.get("/workflows/{workflow_id}")
def get_workflow_endpoint(workflow_id: str):

    workflow = get_workflow(workflow_id)

    if workflow is None:

        return {
            "success": False,
            "error": "Workflow not found.",
        }

    return {
        "success": True,
        "workflow": workflow,
    }