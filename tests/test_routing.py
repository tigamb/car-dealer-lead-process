
from src.routing import route_lead
from src.models import BranchInfo


#========================================================================
# Branch fixture
#========================================================================
# אובייקט סניף לשימוש בכל הטסטים
BRANCH = BranchInfo(
    branch_id="400",
    name="Tel Aviv Showroom",
    manager="David Cohen",
    region="Center",
)


#========================================================================
# HOT Tests
#========================================================================
def test_hot_lead_score_70():
    priority, assigned_to = route_lead(70, BRANCH, "910290")
    assert priority == "HOT"
    assert assigned_to == "David Cohen"

def test_hot_lead_score_100():
    priority, assigned_to = route_lead(100, BRANCH, "910290")
    assert priority == "HOT"
    assert assigned_to == "David Cohen"


#========================================================================
# WARM Tests
#========================================================================
def test_warm_lead_score_40():
    priority, assigned_to = route_lead(40, BRANCH, "910290")
    assert priority == "WARM"
    assert assigned_to == "910290"

def test_warm_lead_score_69():
    priority, assigned_to = route_lead(69, BRANCH, "910290")
    assert priority == "WARM"
    assert assigned_to == "910290"

def test_warm_lead_no_worker_code():
    """אם אין WorkerCode — הולך ל-General Pool"""
    priority, assigned_to = route_lead(50, BRANCH, "")
    assert priority == "WARM"
    assert assigned_to == "General Pool"


#========================================================================
# COLD Tests
#========================================================================
def test_cold_lead_score_39():
    priority, assigned_to = route_lead(39, BRANCH, "910290")
    assert priority == "COLD"
    assert assigned_to == "General Pool"

def test_cold_lead_score_0():
    priority, assigned_to = route_lead(0, BRANCH, "910290")
    assert priority == "COLD"
    assert assigned_to == "General Pool"