"""Evaluation runner for Assignment 2.

Default:
    python evaluator.py

Bonus Gemini LLM-as-a-Judge:
    python evaluator.py --judge

The deterministic evaluator captures the real ADK response and tool calls.
The optional judge uses Gemini to score all four metrics from 0 to 1.
"""

import argparse
import asyncio
import json
import os
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import InMemoryRunner
from google.adk.agents import Agent

from agent import root_agent, INSTRUCTION

load_dotenv()
ROOT = Path(__file__).parent
DATASET = ROOT / "eval_dataset.json"
RESULTS = ROOT / "evaluation_results.json"
METRICS = ["correctness", "relevance", "completeness", "tool_usage"]

# Free Gemini tiers can have low requests-per-minute limits.  The ADK agent
# may make more than one model request for a single test case because it can
# call tools and then ask the model to produce the final answer.  These
# settings deliberately trade speed for reliability.
CASE_DELAY_SECONDS = float(os.getenv("EVAL_CASE_DELAY_SECONDS", "5"))
QUOTA_RETRY_SECONDS = float(os.getenv("EVAL_QUOTA_RETRY_SECONDS", "10"))
MAX_QUOTA_RETRIES = int(os.getenv("EVAL_MAX_QUOTA_RETRIES", "1"))
PRIMARY_MODEL = os.getenv("TRAVEL_AGENT_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODELS = [m.strip() for m in os.getenv(
    "TRAVEL_AGENT_FALLBACK_MODELS",
    "gemini-3.6-flash,gemini-3.5-flash-lite"
).split(",") if m.strip()]

def is_quota_error(exc):
    text = str(exc).lower()
    return any(x in text for x in (
        "resource_exhausted", "quota exceeded", "ratelimit",
        "rate limit", "429", "quota_failure"
    ))

def build_agent(model_name):
    """Build an equivalent evaluator agent using a selected model."""
    return Agent(
        name="travel_planner_eval_agent",
        model=model_name,
        description=root_agent.description,
        instruction=INSTRUCTION,
        tools=list(root_agent.tools),
    )


async def run_case(case, agent):
    runner = InMemoryRunner(agent=agent, app_name="travel_planner_eval")
    user_id = f"eval_{case['id'].lower()}"
    session = await runner.session_service.create_session(
        app_name="travel_planner_eval",
        user_id=user_id,
        session_id=str(uuid.uuid4()),
    )
    message = types.Content(role="user", parts=[types.Part.from_text(text=case["input"])])
    texts, tools = [], []

    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=message):
        content = getattr(event, "content", None)
        if not content:
            continue
        for part in content.parts or []:
            if getattr(part, "text", None):
                texts.append(part.text)
            call = getattr(part, "function_call", None)
            if call and getattr(call, "name", None):
                tools.append(call.name)

    return "\n".join(texts).strip(), sorted(set(tools))


async def run_case_with_fallback(case):
    """Try the primary model, then configured fallbacks, with one slow retry.

    A fallback model is useful when a model-specific RPM/RPD quota is exhausted.
    If the whole project quota is exhausted, no model can guarantee success; in
    that situation the case is recorded as an execution error rather than given
    a fake score.
    """
    models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_exc = None
    for model_index, model_name in enumerate(models):
        agent = build_agent(model_name)
        for attempt in range(MAX_QUOTA_RETRIES + 1):
            try:
                response, tools = await run_case(case, agent)
                return response, tools, model_name
            except Exception as exc:
                last_exc = exc
                if not is_quota_error(exc):
                    raise
                if attempt < MAX_QUOTA_RETRIES:
                    wait = QUOTA_RETRY_SECONDS * (attempt + 1)
                    print(f"  Quota/rate limit on {model_name}. Waiting {wait:.0f}s before retry...")
                    await asyncio.sleep(wait)
                    continue
                if model_index < len(models) - 1:
                    print(f"  Switching from {model_name} -> {models[model_index + 1]}...")
    raise last_exc

def load_cases():
    return json.loads(DATASET.read_text(encoding="utf-8"))["test_cases"]

def has(text, terms):
    t = text.lower()
    return any(term.lower() in t for term in terms)

def deterministic_score(case, response, observed_tools):
    cat = case["category"]
    exp = case["expected_behavior"]
    text = response.lower()
    required = exp.get("expected_points", [])
    score_hits = 0

    if cat == "missing_information":
        missing = exp.get("missing_information", [])
        correctness = 1.0 if has(text, missing) and not has(text, ["here is your itinerary", "day 1"]) else 0.5
        relevance = 1.0 if has(text, missing) else 0.5
        completeness = 1.0 if has(text, missing) else 0.5
    elif cat == "invalid_input":
        field = exp.get("invalid_field")
        field_terms = ["day", "days"] if field == "duration" else ["budget", "positive"]
        correctness = 1.0 if has(text, field_terms) and has(text, ["positive", "invalid", "must"]) else 0.5
        relevance = 1.0 if has(text, field_terms) else 0.5
        completeness = 1.0 if correctness == 1.0 else 0.5
    elif cat == "out_of_scope":
        correctness = 1.0 if not has(text, ["virtual environment", "python -m venv"]) and has(text, ["travel", "trip"]) else 0.4
        relevance = correctness
        completeness = correctness
    else:
        # Expected-point coverage is intentionally transparent and reproducible.
        for p in required:
            keywords = {
                "Provides a 3-day itinerary": ["day 1", "day 2", "day 3"],
                "Provides a 5-day itinerary": ["day 1", "day 2", "day 3", "day 4", "day 5"],
                "Provides a 2-day itinerary": ["day 1", "day 2"],
                "Includes Jaipur attractions": ["jaipur", "amber", "hawa mahal", "city palace"],
                "Includes Delhi monuments": ["red fort", "qutub", "humayun", "jama masjid"],
                "Includes markets": ["market", "chandni chowk", "bazaar"],
                "Prioritizes historical places": ["history", "historical", "fort", "palace", "monument"],
                "Includes local food suggestions": ["food", "kachori", "dal baati", "local"],
                "Includes local food": ["food", "paratha", "jalebi", "local"],
                "Considers the ₹15,000 budget": ["15000", "15,000", "budget"],
                "Considers the ₹25,000 budget": ["25000", "25,000", "budget"],
                "Considers the ₹18,000 budget": ["18000", "18,000", "budget"],
                "Considers the ₹10,000 budget": ["10000", "10,000", "budget"],
                "Attempts to stay within ₹5,000": ["5000", "5,000", "budget", "tight", "cheap"],
                "Keeps recommendations budget-friendly": ["budget", "cheap", "low-cost", "tight"],
                "Uses low-cost activities and food suggestions": ["cheap", "low-cost", "free", "budget"],
                "Includes historical places": ["history", "historical", "palace"],
                "Includes lakes": ["lake", "pichola"],
                "Includes photography-friendly locations": ["photo", "photography", "scenic"],
                "Includes food-focused recommendations": ["food", "paratha", "jalebi", "street"],
                "Includes local cuisine": ["local", "cuisine", "paratha"],
                "Includes street-food suggestions": ["street", "food", "old delhi"],
            }.get(p, [p])
            if has(text, keywords):
                score_hits += 1
        coverage = score_hits / max(1, len(required))
        correctness = round(0.4 + 0.6 * coverage, 2)
        relevance = round(min(1.0, 0.5 + 0.5 * coverage), 2)
        structure = sum(x in text for x in ["budget", "day 1", "recommended", "tips"])
        completeness = round(min(1.0, structure / 4), 2)

    expected_tools = set(case.get("expected_tools", []))
    actual_tools = set(observed_tools)
    tool_usage = 1.0 if not expected_tools and not actual_tools else (
        round(len(expected_tools & actual_tools) / len(expected_tools), 2) if expected_tools else 0.0
    )

    scores = {
        "correctness": round(correctness, 2),
        "relevance": round(relevance, 2),
        "completeness": round(completeness, 2),
        "tool_usage": round(tool_usage, 2),
    }
    scores["overall"] = round(sum(scores.values()) / 4, 4)
    return scores

async def llm_judge_all(cases_and_results):
    """Bonus judge: ONE Gemini call for all cases to minimize quota usage."""
    from google import genai
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is required for --judge.")
    client = genai.Client(api_key=key)
    judge_models = [m.strip() for m in os.getenv(
        "EVAL_JUDGE_FALLBACK_MODELS",
        "gemini-3.6-flash,gemini-3.5-flash-lite"
    ).split(",") if m.strip()]
    primary = os.getenv("EVAL_JUDGE_MODEL", "gemini-3.8-flash")
    models = [primary] + [m for m in judge_models if m != primary]
    payload = []
    for item in cases_and_results:
        payload.append({
            "test_case_id": item["test_case_id"],
            "input": item["input"],
            "expected_behavior": item["expected_behavior"],
            "expected_tools": item.get("expected_tools", []),
            "observed_tools": item["observed_tools"],
            "actual_response": item["actual_response"],
        })
    prompt = f"""You are an evaluator for a Travel Planner Agent.
Score each test case on exactly four metrics from 0 to 1: correctness, relevance, completeness, tool_usage.
Return ONLY a JSON array. Each object must contain test_case_id, correctness, relevance, completeness, tool_usage, reason.
Do not invent missing observations.

Cases:
{json.dumps(payload, ensure_ascii=False)}
"""
    last_exc = None
    for model_index, model_name in enumerate(models):
        try:
            result = client.models.generate_content(model=model_name, contents=prompt)
            raw = re.sub(r"^```json\s*|\s*```$", "", result.text.strip(), flags=re.I)
            data = json.loads(raw)
            return data, model_name
        except Exception as exc:
            last_exc = exc
            if not is_quota_error(exc) or model_index == len(models) - 1:
                raise
            print(f"  Judge quota on {model_name}; switching to {models[model_index + 1]}...")
    raise last_exc

async def main(judge=False):
    results = []
    cases = load_cases()
    for index, case in enumerate(cases):
        print(f"Running {case['id']}...")
        try:
            response, tools, model_used = await run_case_with_fallback(case)
            scores = deterministic_score(case, response, tools)
            reason = "Deterministic rubric based on expected behavior and observed ADK tool calls."
            if judge:
                # Bonus judging is performed once after all deterministic cases.
                pass
            results.append({
                "test_case_id": case["id"],
                "category": case["category"],
                "input": case["input"],
                "expected_behavior": case["expected_behavior"],
                "expected_tools": case.get("expected_tools", []),
                "actual_response": response,
                "observed_tools": tools,
                "model_used": model_used,
                "scores": scores,
                "overall_percentage": round(scores["overall"] * 100, 1),
                "passed": scores["overall"] >= 0.75,
                "reason": reason,
            })
            print(f"  Overall: {scores['overall']*100:.1f}%")
            if index < len(cases) - 1:
                print(f"  Waiting {CASE_DELAY_SECONDS:.0f}s before the next test case to protect API quota...")
                await asyncio.sleep(CASE_DELAY_SECONDS)
        except Exception as exc:
            results.append({
                "test_case_id": case["id"],
                "category": case["category"],
                "input": case["input"],
                "expected_behavior": case["expected_behavior"],
                "actual_response": "",
                "observed_tools": [],
                "model_used": None,
                "scores": {m: 0.0 for m in METRICS} | {"overall": 0.0},
                "overall_percentage": 0.0,
                "passed": False,
                "reason": f"Execution error: {type(exc).__name__}: {exc}",
            })
            print(f"  ERROR: {exc}")
            if index < len(cases) - 1:
                print(f"  Waiting {CASE_DELAY_SECONDS:.0f}s before the next test case...")
                await asyncio.sleep(CASE_DELAY_SECONDS)

    judge_model_used = None
    if judge:
        judge_data, judge_model_used = await llm_judge_all(results)
        by_id = {str(x.get("test_case_id")): x for x in judge_data}
        for item in results:
            judged = by_id.get(item["test_case_id"])
            if not judged:
                continue
            scores = {m: round(max(0.0, min(1.0, float(judged[m]))), 2) for m in METRICS}
            scores["overall"] = round(sum(scores[m] for m in METRICS) / 4, 4)
            item["scores"] = scores
            item["overall_percentage"] = round(scores["overall"] * 100, 1)
            item["passed"] = scores["overall"] >= 0.75
            item["reason"] = judged.get("reason", "LLM judge")

    overall = sum(r["scores"]["overall"] for r in results) / len(results)
    metric_averages = {m: round(sum(r["scores"][m] for r in results) / len(results), 4) for m in METRICS}
    failed = [r["test_case_id"] for r in results if not r["passed"]]

    output = {
        "project": "Personal Travel Planner Agent",
        "evaluation_version": "1.0",
        "judge_enabled": judge,
        "judge_model_used": judge_model_used,
        "primary_model": PRIMARY_MODEL,
        "fallback_models": FALLBACK_MODELS,
        "summary": {
            "total_test_cases": len(results),
            "passed_test_cases": sum(r["passed"] for r in results),
            "failed_test_cases": len(failed),
            "overall_score": round(overall, 4),
            "overall_percentage": round(overall * 100, 1),
            "metric_averages": metric_averages,
            "failed_case_ids": failed,
        },
        "results": results,
    }
    RESULTS.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nOverall Evaluation Score: {overall*100:.1f}%")
    print(f"Results written to {RESULTS}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.judge))
