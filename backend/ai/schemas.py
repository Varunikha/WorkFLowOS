from typing import List
from pydantic import BaseModel, Field


class WorkflowAction(BaseModel):
    application: str = Field(
        description="Application or website involved in the action."
    )

    action: str = Field(
        description="What the user does in that application."
    )


class WorkflowCondition(BaseModel):
    condition: str = Field(
        description="Condition that should be checked."
    )

    otherwise: str = Field(
        description="What should happen if the condition is not satisfied."
    )


class WorkflowTrigger(BaseModel):
    type: str = Field(
        description="Type of trigger, for example repeated_sequence or event."
    )

    description: str = Field(
        description="Human-readable description of what starts the workflow."
    )


class WorkflowUnderstanding(BaseModel):
    intent: str = Field(
        description="Meaningful name describing the user's overall intent."
    )

    summary: str = Field(
        description="Short explanation of what the user is trying to accomplish."
    )

    trigger: WorkflowTrigger

    variables: List[str] = Field(
        default_factory=list,
        description="Important values that may change between executions."
    )

    actions: List[WorkflowAction] = Field(
        default_factory=list
    )

    conditions: List[WorkflowCondition] = Field(
        default_factory=list
    )