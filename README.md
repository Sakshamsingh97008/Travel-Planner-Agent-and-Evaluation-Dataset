# Travel Planner Agent — Assignment 2 Evaluation

## Objective

Evaluate the Travel Planner Agent developed in Assignment 1 and measure how well it performs across different user requests.

The Assignment 1 system under test is a Google ADK agent with three grounding tools:
- `get_destination_info`
- `estimate_budget`
- `sum_entry_fees`

The evaluation compares each actual agent response against an expected behavior and scores:
1. Correctness
2. Relevance
3. Completeness
4. Tool Usage

Each metric is scored from 0 to 1.

## Project Structure

```text
travel-planner/
├── agent.py
├── eval_dataset.json
├── evaluator.py
├── evaluation_results.json
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

## Test Dataset

The dataset contains the 10 required test cases:

| ID | Category | Scenario |
|---|---|---|
| TC01 | Normal travel request | 3-day Jaipur, ₹15,000, history + food |
| TC02 | Normal travel request | 5-day Delhi, ₹25,000, monuments + markets + food |
| TC03 | Low budget | 3-day Agra, ₹5,000 |
| TC04 | Missing information | Missing destination |
| TC05 | Missing information | Missing budget |
| TC06 | Invalid input | 0-day trip |
| TC07 | Invalid input | Negative budget |
| TC08 | User preference | Udaipur, history + lakes + photography |
| TC09 | Food preference | Delhi, street food + local cuisine |
| TC10 | Out of scope | Python virtual-environment question |

### Important Assignment 1 compatibility note

The original Assignment 1 curated destination data contains Jaipur, Udaipur, Delhi and Goa. TC03 deliberately uses **Agra** to test how the agent handles a destination outside its curated knowledge base, because the Assignment 1 instructions say that if destination data is `not_found`, the agent should use general knowledge and clearly state that the details are not from the curated list.

## Evaluation Approach

For every test case:

1. Send the exact dataset input to the actual ADK agent.
2. Capture the final response.
3. Capture the ADK function/tool calls.
4. Compare the response with expected behavior.
5. Score four metrics from 0–1.
6. Calculate the test-case overall score.
7. Calculate the overall evaluation score across all cases.
8. Record failed test cases and reasons.

### Scoring formula

```text
Test Case Overall =
(Correctness + Relevance + Completeness + Tool Usage) / 4
```

```text
Overall Evaluation Score =
Average(Test Case Overall scores)
```

## Metrics

### Correctness

Does the agent satisfy the user's request and correctly handle missing/invalid information?

### Relevance

Does the response stay focused on the travel request or correctly redirect an out-of-scope request?

### Completeness

Does the response contain the important requested information, such as duration, attractions, preferences, budget and day-wise planning?

### Tool Usage

Did the agent invoke the appropriate Assignment 1 tool when required?

For valid travel requests, the expected tool set is:

```text
get_destination_info
estimate_budget
sum_entry_fees
```

For missing required information, invalid inputs and the out-of-scope test, no travel-planning tools are expected.

## Setup

### 1. Create environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure `.env`

Copy `.env.example`:

```powershell
copy .env.example .env
```

Then add your own Gemini key:

```env
GOOGLE_API_KEY=YOUR_REAL_GEMINI_API_KEY
TRAVEL_AGENT_MODEL=gemini-3.8-flash
EVAL_JUDGE_MODEL=gemini-3.8-flash
```

Never commit `.env`.

## Run the Agent

```powershell
adk web
```

## Run Evaluation

Deterministic evaluator:

```powershell
python evaluator.py
```

The actual agent responses and scores are written to:

```text
evaluation_results.json
```


### Quota-safe evaluation

The evaluator runs test cases sequentially and waits between cases because one ADK test case can generate multiple Gemini model requests (for example, a model request, tool call, and final response). The default delay is 45 seconds between cases. If Gemini returns a temporary quota/rate-limit error, the evaluator waits 90 seconds, retries once, and then switches to configured fallback models.

You can adjust these settings and fallback models in `.env` if needed:

```env
TRAVEL_AGENT_MODEL=gemini-3.8-flash
TRAVEL_AGENT_FALLBACK_MODELS=gemini-3.6-flash,gemini-3.5-flash-lite
EVAL_CASE_DELAY_SECONDS=45
EVAL_QUOTA_RETRY_SECONDS=90
EVAL_MAX_QUOTA_RETRIES=1
```

If a Gemini error says `RESOURCE_EXHAUSTED` with a per-minute quota, do not repeatedly restart the evaluator. Let the built-in retry/wait logic run. The bonus `--judge` mode uses additional Gemini requests and should only be run when sufficient quota is available.

### Bonus: Gemini LLM-as-a-Judge

```powershell
python evaluator.py --judge
```

The Gemini judge scores all four metrics and provides a reason.

Example output format:

```text
Test Case: TC01
Correctness: 0.90
Relevance: 1.00
Completeness: 0.80
Tool Usage: 1.00
Overall Score: 92.5%
Reason: The agent correctly produced the requested itinerary...
```

The numbers above are an **example format only**. The submission score must come from the real evaluation run.

## Failed Test Cases

`evaluation_results.json` automatically contains:

- failed case IDs
- actual response
- expected behavior
- observed tools
- individual metric scores
- overall score
- failure reason

A test case passes when its overall score is at least 0.75.

## Failure Analysis

Potential failure patterns include:

1. Missing destination/budget is not requested.
2. Zero or negative values are accepted.
3. Required tools are skipped.
4. User preferences are not reflected in attraction selection.
5. The requested number of days is not covered.
6. Budget information is not incorporated.
7. Out-of-scope questions are answered instead of redirected.

## Suggestions for Improving the Agent

Based on evaluation results:

- Add explicit numeric validation for days and budget before planning.
- Add stronger scope control for non-travel questions.
- Require all three tools for valid complete travel requests.
- Improve preference extraction for history, food, lakes, photography, shopping and beaches.
- Ensure the number of itinerary days exactly matches the requested duration.
- Expand the curated destination database.
- Add regression tests whenever the agent prompt or tools change.
- Keep tool-call traces as part of evaluation evidence.

## Overall Score

Do not manually invent the overall score.

After:

```powershell
python evaluator.py
```

or:

```powershell
python evaluator.py --judge
```

copy the real `overall_percentage` from `evaluation_results.json` into this README if your instructor requires the number directly in the document.

## Learning Outcome

```text
Assignment 1 → Build an Agent
Assignment 2 → Evaluate the Agent
             → Measure Performance
             → Identify Failures
             → Improve the Agent
```

## Author

Saksham Singh

## Quota-safe evaluation and fallback models

The evaluator is designed for Gemini free-tier environments where model-specific request limits can be low. It runs test cases sequentially with a configurable delay, detects quota/rate-limit failures, retries after a long backoff, and then switches to fallback models.

Default order:
1. `gemini-3.8-flash`
2. `gemini-3.6-flash`
3. `gemini-3.5-flash-lite`

Configure these through `TRAVEL_AGENT_MODEL` and `TRAVEL_AGENT_FALLBACK_MODELS` in `.env`.

The optional `--judge` mode is also quota-conscious: instead of making one judge request per test case, it sends the ten completed cases in one Gemini request and has judge-model fallbacks.

A fallback cannot bypass a project-wide quota. If the whole project is exhausted, the evaluator records an execution error rather than fabricating a score. Google recommends client-side retry/backoff for rate-limit errors; model-specific quotas can differ by model. See the Gemini API rate-limit documentation for current limits.

## Recommended run

```powershell
python evaluator.py
```

Only after the ten deterministic cases complete successfully should you optionally run:

```powershell
python evaluator.py --judge
```

If a free-tier quota is exhausted, wait for the quota window to reset rather than repeatedly restarting the evaluator. The evaluator already retries and rotates models.
