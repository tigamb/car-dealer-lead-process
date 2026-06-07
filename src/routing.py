"""
Lead Routing Module.

Routes a lead based on its score:
  Score >= 70  → HOT  → assigned to branch manager
  Score 40-69  → WARM → assigned to worker (WorkerCode from lead)
  Score < 40   → COLD → assigned to general pool
"""

from typing import Tuple
from src.models import BranchInfo


def route_lead(
    score: int,
    branch_info: BranchInfo,
    worker_code: str,
) -> Tuple[str, str]:
    """
    קובע עדיפות וסוכן אחראי לליד לפי הציון.
    
    Returns:
        Tuple של (priority, assigned_to)
    """
    if score >= 70:
        return "HOT", branch_info.manager

    if score >= 40:
        assigned = worker_code if worker_code else "General Pool"
        return "WARM", assigned

    return "COLD", "General Pool"