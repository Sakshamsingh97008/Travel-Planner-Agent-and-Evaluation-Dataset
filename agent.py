"""Personal Travel Planner Agent - Assignment 1 system under evaluation."""

import os
from google.adk.agents import Agent
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("TRAVEL_AGENT_MODEL", "gemini-3.8-flash")

DESTINATIONS = {
    "jaipur": {
        "places": [
            {"name": "Amber Fort", "tags": ["history", "architecture", "views"], "fee_inr": 100, "hours": 3, "area": "Amer (11 km north)", "tip": "Go at opening time to beat crowds and heat."},
            {"name": "City Palace", "tags": ["history", "architecture", "culture"], "fee_inr": 200, "hours": 2, "area": "Old City", "tip": "Still home to the royal family; museum wings are worth it."},
            {"name": "Hawa Mahal", "tags": ["history", "architecture"], "fee_inr": 50, "hours": 1, "area": "Old City", "tip": "Best photographed from the cafes across the road in the morning."},
            {"name": "Jantar Mantar", "tags": ["history", "science"], "fee_inr": 50, "hours": 1, "area": "Old City", "tip": "UNESCO site; a guide adds a lot of value."},
            {"name": "Jaigarh Fort", "tags": ["history", "views"], "fee_inr": 70, "hours": 2, "area": "Above Amber", "tip": "Home to the world's largest cannon on wheels."},
            {"name": "Nahargarh Fort", "tags": ["history", "views"], "fee_inr": 50, "hours": 2, "area": "Aravalli ridge", "tip": "Go for sunset over the city."},
            {"name": "Albert Hall Museum", "tags": ["history", "culture", "architecture"], "fee_inr": 40, "hours": 1.5, "area": "Ram Niwas Garden", "tip": "Looks stunning lit up in the evening."},
            {"name": "Jal Mahal", "tags": ["views", "architecture"], "fee_inr": 0, "hours": 0.5, "area": "Man Sagar Lake", "tip": "Photo stop only; the palace is closed to visitors."},
            {"name": "Johari Bazaar", "tags": ["shopping", "culture"], "fee_inr": 0, "hours": 2, "area": "Old City", "tip": "Jewellery, textiles, and bargaining practice."},
            {"name": "Bapu Bazaar", "tags": ["shopping", "culture"], "fee_inr": 0, "hours": 2, "area": "Old City", "tip": "Juttis, block prints, and lac bangles."},
        ],
        "food": [
            {"dish": "Pyaaz Kachori", "where": "Rawat Mishthan Bhandar", "approx_cost_inr": 60},
            {"dish": "Dal Baati Churma", "where": "Laxmi Misthan Bhandar (LMB) or Chokhi Dhani", "approx_cost_inr": 350},
            {"dish": "Laal Maas", "where": "Handi Restaurant / local Rajasthani eateries", "approx_cost_inr": 450},
            {"dish": "Ghewar (seasonal sweet)", "where": "Old City sweet shops", "approx_cost_inr": 150},
            {"dish": "Mango/sweet lassi", "where": "Lassiwala, MI Road", "approx_cost_inr": 60},
            {"dish": "Masala chai + street snacks", "where": "Masala Chowk food court", "approx_cost_inr": 150},
        ],
        "stay_tip": "Stay near MI Road, Bani Park or C-Scheme for good value and easy cabs."
    },
    "udaipur": {
        "places": [
            {"name": "City Palace Udaipur", "tags": ["history", "architecture", "views"], "fee_inr": 300, "hours": 2.5, "area": "Pichola lakefront", "tip": "Largest palace complex in Rajasthan."},
            {"name": "Jagdish Temple", "tags": ["history", "culture"], "fee_inr": 0, "hours": 1, "area": "Old City", "tip": "Right next to City Palace."},
            {"name": "Lake Pichola boat ride", "tags": ["views", "romance", "nature"], "fee_inr": 400, "hours": 1, "area": "Pichola", "tip": "Take the sunset slot."},
            {"name": "Saheliyon ki Bari", "tags": ["nature", "history"], "fee_inr": 50, "hours": 1, "area": "Fatehsagar", "tip": "Fountain garden, calm in the morning."},
            {"name": "Sajjangarh (Monsoon Palace)", "tags": ["views", "history"], "fee_inr": 250, "hours": 2, "area": "Hilltop", "tip": "Best sunset viewpoint in the city."},
        ],
        "food": [
            {"dish": "Dal Baati Churma", "where": "Old City thali restaurants", "approx_cost_inr": 300},
            {"dish": "Mirchi Vada & Kachori", "where": "Local sweet-and-snack shops", "approx_cost_inr": 60},
            {"dish": "Rooftop dinner with lake view", "where": "Ambrai Ghat area", "approx_cost_inr": 700},
        ],
        "stay_tip": "Lal Ghat / Gangaur Ghat guesthouses give lake views."
    },
    "delhi": {
        "places": [
            {"name": "Red Fort", "tags": ["history", "architecture"], "fee_inr": 35, "hours": 2, "area": "Old Delhi", "tip": "Closed on Mondays."},
            {"name": "Humayun's Tomb", "tags": ["history", "architecture"], "fee_inr": 40, "hours": 1.5, "area": "Nizamuddin", "tip": "Forerunner of the Taj Mahal's design."},
            {"name": "Qutub Minar", "tags": ["history", "architecture"], "fee_inr": 40, "hours": 1.5, "area": "Mehrauli", "tip": "Pair with Mehrauli Archaeological Park."},
            {"name": "India Gate", "tags": ["history", "views"], "fee_inr": 0, "hours": 1, "area": "Central Delhi", "tip": "Lovely in the evening."},
            {"name": "Jama Masjid", "tags": ["history", "culture", "architecture"], "fee_inr": 0, "hours": 1, "area": "Old Delhi", "tip": "Dress modestly; camera fee applies."},
            {"name": "Chandni Chowk", "tags": ["food", "shopping", "culture"], "fee_inr": 0, "hours": 3, "area": "Old Delhi", "tip": "Walk it; rickshaws get stuck."},
        ],
        "food": [
            {"dish": "Stuffed parathas", "where": "Paranthe Wali Gali", "approx_cost_inr": 150},
            {"dish": "Butter chicken / kebabs", "where": "Karim's, Jama Masjid", "approx_cost_inr": 400},
            {"dish": "Jalebi", "where": "Old Famous Jalebi Wala", "approx_cost_inr": 60},
        ],
        "stay_tip": "Paharganj and Karol Bagh are budget-friendly and close to the metro."
    },
    "goa": {
        "places": [
            {"name": "Baga & Calangute beaches", "tags": ["beach", "nightlife", "nature"], "fee_inr": 0, "hours": 3, "area": "North Goa", "tip": "Lively; go early for quieter sands."},
            {"name": "Palolem Beach", "tags": ["beach", "nature", "views"], "fee_inr": 0, "hours": 3, "area": "South Goa", "tip": "Calmer and scenic."},
            {"name": "Fort Aguada", "tags": ["history", "views"], "fee_inr": 0, "hours": 1.5, "area": "North Goa", "tip": "Sunset views over the sea."},
            {"name": "Old Goa churches (Basilica of Bom Jesus)", "tags": ["history", "architecture", "culture"], "fee_inr": 0, "hours": 2, "area": "Old Goa", "tip": "UNESCO World Heritage site."},
            {"name": "Fontainhas Latin Quarter", "tags": ["history", "culture", "photography"], "fee_inr": 0, "hours": 1.5, "area": "Panjim", "tip": "Colourful Portuguese-era lanes."},
        ],
        "food": [
            {"dish": "Goan fish thali", "where": "Local 'Ghar' style eateries", "approx_cost_inr": 300},
            {"dish": "Pork vindaloo / Xacuti", "where": "Panjim restaurants", "approx_cost_inr": 400},
            {"dish": "Bebinca", "where": "Local bakeries", "approx_cost_inr": 120},
        ],
        "stay_tip": "Hostels and homestays are available in both North and South Goa."
    },
}

def get_destination_info(city: str, interests: str = "") -> dict:
    key = city.strip().lower()
    data = DESTINATIONS.get(key)
    if not data:
        return {
            "status": "not_found",
            "message": f"No curated data for '{city}'. Supported: {', '.join(k.title() for k in DESTINATIONS)}.",
        }
    wanted = interests.lower()
    def score(place: dict) -> int:
        return sum(1 for tag in place["tags"] if tag in wanted)
    ranked = sorted(data["places"], key=score, reverse=True)
    return {
        "status": "success",
        "city": city.title(),
        "places": [
            {k: v for k, v in p.items() if k != "tags"} | {"matches_interests": score(p) > 0}
            for p in ranked
        ],
        "food": data["food"],
        "stay_tip": data["stay_tip"],
        "note": "Entry fees are approximate and may change; verify before travel.",
    }

def estimate_budget(days: int, total_budget_inr: float, travelers: int = 1, intercity_travel_inr: float = 0) -> dict:
    if days < 1 or total_budget_inr <= 0 or travelers < 1:
        return {"status": "error", "message": "days, budget and travelers must be positive."}
    usable = total_budget_inr - intercity_travel_inr
    if usable <= 0:
        return {"status": "error", "message": "Intercity travel alone exceeds the budget."}
    split = {"stay": 0.35, "food": 0.25, "local_transport": 0.15, "entry_fees_and_activities": 0.15, "buffer": 0.10}
    breakdown = {name: round(usable * share) for name, share in split.items()}
    per_person_per_day = usable / days / travelers
    if per_person_per_day < 1500:
        verdict = "very tight - stick to hostels, local food and free sights"
    elif per_person_per_day < 3000:
        verdict = "tight but doable - budget stays and mostly local transport"
    else:
        verdict = "comfortable - room for nicer stays and a few paid experiences"
    return {
        "status": "success",
        "usable_budget_inr": round(usable),
        "intercity_travel_inr": round(intercity_travel_inr),
        "breakdown_inr": breakdown,
        "per_day_inr": round(usable / days),
        "per_person_per_day_inr": round(per_person_per_day),
        "verdict": verdict,
    }

def sum_entry_fees(city: str, place_names: list[str], travelers: int = 1) -> dict:
    data = DESTINATIONS.get(city.strip().lower())
    if not data:
        return {"status": "not_found", "message": f"No fee data for '{city}'."}
    fees, unmatched = {}, []
    for wanted in place_names:
        match = next(
            (p for p in data["places"]
             if wanted.lower() in p["name"].lower() or p["name"].lower() in wanted.lower()),
            None,
        )
        if match:
            fees[match["name"]] = match["fee_inr"] * travelers
        else:
            unmatched.append(wanted)
    return {
        "status": "success",
        "fees_inr": fees,
        "total_inr": sum(fees.values()),
        "unmatched": unmatched,
        "note": "Approximate Indian-resident rates; foreign-visitor tickets cost more.",
    }

INSTRUCTION = """
You are a friendly, practical Personal Travel Planner for trips within India.

STEP 1 - UNDERSTAND. Extract: destination, number of days, total budget (INR),
number of travelers, interests, and whether the budget includes travel to the
destination. If the destination, days or budget is missing, ask ONE short
message listing only what is missing. Otherwise do not ask questions; state
any assumption in one line.

STEP 2 - GATHER DATA. Call tools, do not guess numbers:
1. get_destination_info(city, interests) for places and food.
2. estimate_budget(days, total_budget_inr, travelers, intercity_travel_inr).
3. sum_entry_fees(city, place_names, travelers) for the places you pick.
If get_destination_info returns "not_found", use general knowledge and clearly
say the details are not from the curated list.

STEP 3 - PLAN.
- Group places by area to reduce travel time; 2-4 sights per day.
- Prioritise places that match stated interests.
- Put hot-weather outdoor sights in the morning.
- Include a meal suggestion for each day from the food list.
- If the budget verdict is "very tight", favour free sights and cheap eats
  and say what was left out.

STEP 4 - RESPOND in this exact structure:
**Trip summary** (destination, days, budget, travelers, interests, assumptions)
**Budget estimate** (table: category, amount in Rs; tie it to tool output;
include total entry fees; mention if the plan stays within budget)
**Recommended places** (short list with one-line reason each)
**Day-wise plan** (Day 1 / Day 2 / ...; Morning, Afternoon, Evening, plus
the day's approximate spend)
**Tips** (2-3 practical tips)

RULES: Use Rs amounts. Label all prices "approx.". Keep the whole answer
concise and scannable. If the user later changes days, budget or interests,
re-run relevant tools and update the plan.
"""

root_agent = Agent(
    name="travel_planner_agent",
    model=MODEL,
    description="Plans day-wise travel itineraries within a budget for trips in India.",
    instruction=INSTRUCTION,
    tools=[get_destination_info, estimate_budget, sum_entry_fees],
)
