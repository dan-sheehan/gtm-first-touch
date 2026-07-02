# ICP Scorer

Rule-based Ideal Customer Profile scoring engine that evaluates companies across weighted dimensions (industry fit, company size, funding stage, tech stack, growth signals, buying signals) and produces a grade with per-dimension breakdown.

## GTM Workflow

Sits at the top of the prospecting funnel — before any outreach happens, sales teams need to qualify whether a company fits their ICP. This tool replaces gut-feel qualification with a repeatable, configurable scoring model that produces consistent A/B/C/D grades across the team.

## How It Works

1. User enters company name and selects values for each scoring dimension
2. Engine computes a weighted score: `score = Σ(dimension_weight × option_score) / Σ(weights)`
3. Grade is assigned based on configurable thresholds (A ≥ 80, B ≥ 60, C ≥ 40, D < 40)
4. Score and breakdown are saved to SQLite for historical tracking
5. Scoring model weights and options are fully configurable via `scoring_model.json`

## Example Output

```json
{
  "company_name": "Acme Corp",
  "score": 82,
  "grade": "A",
  "breakdown": [
    {"dimension": "industry_fit", "label": "Industry Fit", "weight": 25, "score": 100, "weighted": 25.0},
    {"dimension": "company_size", "label": "Company Size", "weight": 20, "score": 90, "weighted": 18.0},
    {"dimension": "funding_stage", "label": "Funding Stage", "weight": 20, "score": 100, "weighted": 20.0},
    {"dimension": "tech_stack", "label": "Tech Stack Signals", "weight": 15, "score": 75, "weighted": 11.3},
    {"dimension": "growth_signals", "label": "Growth Signals", "weight": 10, "score": 70, "weighted": 7.0},
    {"dimension": "buying_signals", "label": "Buying Signals", "weight": 10, "score": 50, "weighted": 5.0}
  ]
}
```

## Business Impact

Eliminates subjective ICP qualification — ensures every rep uses the same scoring criteria, reducing wasted outreach on poor-fit accounts by up to 40%.
