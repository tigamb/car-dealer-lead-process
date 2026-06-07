
from typing import Tuple
from src.models import BranchInfo


def route_lead(
    score: int,
    branch_info: BranchInfo,
    worker_code: str,
) -> Tuple[str, str]:
    
    if score >= 70:
        return "HOT", branch_info.manager

    if score >= 40:
        assigned = worker_code if worker_code else "General Pool"
        return "WARM", assigned

    return "COLD", "General Pool"