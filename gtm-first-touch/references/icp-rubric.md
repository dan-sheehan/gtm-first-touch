# Example ICP rubric

This optional rubric preserves the prototype's six dimensions, weights, known-option scores, and grade thresholds. It favors growth-stage technology companies. It is an **illustration for a particular seller**, not a universal B2B ICP or the workflow's default. Use it only after the user selects it; adapt criteria to the actual offer when requested.

The [canonical workflow](../workflow.md) governs scoring. Scores are decision aids. Research, classification, and interpretation can vary between runs, even with fixed weights. A high fit score does not establish buying intent, budget, or likelihood of purchase.

## Dimensions and options

Choose one supported option per dimension. The scores below are illustrative preferences, not externally validated predictions.

| Dimension | Weight | Known options and scores |
| --- | ---: | --- |
| Industry fit | 25 | SaaS / software: 100; fintech: 90; healthtech: 75; e-commerce: 70; marketplace: 65; other tech: 50; non-tech: 20 |
| Company size | 20 | 1–10 employees: 30; 11–50: 60; 51–200: 100; 201–500: 90; 501–1000: 70; more than 1000: 40 |
| Funding stage | 20 | Seed: 50; Series A: 90; Series B: 100; Series C+: 75; bootstrapped: 40; public: 30 |
| Technology fit | 15 | Modern stack with relevant analytics tools: 100; modern stack with limited relevant tooling: 75; legacy stack with active migration: 60; legacy stack: 30 |
| Growth signals | 10 | Strong hiring and recent funding: 100; steady hiring and stable growth: 70; flat or slow growth: 40; contraction or downsizing: 15 |
| Buying signals | 10 | Active evaluation / RFP: 100; inbound interest: 85; relevant new technology adoption: 70; engagement with seller content: 50; no buying signal found in the material reviewed: 15 |

“Modern,” “relevant,” “strong,” and “recent” require judgment in the context of the offer and research date. Explain the interpretation and cite the evidence. Do not infer new adoption from an undated tools list, content engagement from a job title, or intent from funding.

If several categories could apply, explain the selection. If ambiguity could change the assessment and cannot be resolved, leave it unscored. A user can supply a more suitable rubric instead.

## Calculation

For complete inputs, calculate:

```text
score = sum(weight × option score) / sum(weights)
```

These weights sum to 100. Show each contribution and the total to one decimal place. Assign grades using the unrounded total:

| Grade | Threshold |
| --- | --- |
| A | 80 or above |
| B | 60 to below 80 |
| C | 40 to below 60 |
| D | Below 40 |

These labels express this rubric's preferences only. State exclusions separately and pair the score with a reasoned recommendation.

## Missing evidence

All dimensions can be **unknown / unscored**. If any required dimension is unresolved, show the known dimension results and leave the overall score and grade pending. The prototype assigned low points to some unknowns; this version removes those penalties so lack of research is not presented as poor fit.

“No buying signal found” is a narrow observation about material actually reviewed. The user must choose that option knowingly after such a review. It does not mean the company has no buying intent. With no review or conflicting evidence, use unknown instead.

## Worked example

The [Harbor walkthrough](../examples/harbor-analytics.md) supplies fictional inputs and selected options. Its score is 91.5, grade A, under this rubric. That is high illustrative fit with **no demonstrated buying intent**. The example explains why it does not reuse the prototype's seeded 84.
