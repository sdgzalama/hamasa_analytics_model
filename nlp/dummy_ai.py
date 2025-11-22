import random
import uuid

# Dummy lists of possible values
INDUSTRIES = [
    "Food Manufacturers", "Soft Drinks Companies", "Fast Food Chains",
    "Agriculture Input Suppliers", "Supermarkets", "Media Houses"
]

TACTICS = [
    "Policy lobbying", "Corporate Social Responsibility (CSR)",
    "Front groups", "Funding research", "Marketing to children",
    "Political influence", "Regulatory delay"
]

STAKEHOLDERS = [
    "Consumers", "Government agencies", "Farmers",
    "Health advocates", "Youth", "Women groups", "Civil society"
]

POLICIES = [
    "Front-of-Pack Warning Labels", "Taxation on Sugary Drinks",
    "Marketing restrictions", "Food fortification policy",
    "Nutrition guidelines", "School feeding regulations"
]

LOCATIONS = [
    "Dar es Salaam", "Dodoma", "Arusha", "Mwanza",
    "Zanzibar", "Morogoro", "Tanga", "Mbeya", "Regional level", "National level"
]

IMPACTS = [
    "Influenced public opinion", "Delayed policy adoption",
    "Increased awareness", "Created controversy",
    "Strengthened government stance", "Confused citizens"
]


def generate_dummy_analysis():
    """
    Returns fake analysis data to simulate AI output.
    """
    return {
        "industry_name": random.choice(INDUSTRIES),
        "industry_tactic": random.choice(TACTICS),
        "stakeholders": random.sample(STAKEHOLDERS, 2),
        "targeted_policy": random.choice(POLICIES),
        "geographical_focus": random.choice(LOCATIONS),
        "outcome_impact": random.choice(IMPACTS),
        "semantic_area_ids": [str(uuid.uuid4())],
    }
