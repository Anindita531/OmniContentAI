from typing import TypedDict, List

class AgentState(TypedDict):
    task: str                # Initial user request
    content: str             # Current draft
    feedback: str            # Feedback from Compliance
    iterations: int          # Counter to prevent infinite loops
    is_compliant: bool       # Final flag