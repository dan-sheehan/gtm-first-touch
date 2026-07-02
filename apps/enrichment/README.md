# Enrichment Chain

Multi-step company enrichment pipeline that runs sequential AI-powered research passes — web research, tech stack detection, funding signals, and competitive landscape — where each step's output feeds as context into the next.

## GTM Workflow

Automates the top-of-funnel enrichment workflow that RevOps teams typically cobble together from 4-5 different data providers (ZoomInfo, Clearbit, BuiltWith, Crunchbase). Each provider step is defined in `providers.json` with its own prompt template, making the pipeline configurable and extensible without code changes.

## How It Works

1. User enters a company name
2. Pipeline runs 4 sequential enrichment steps through the configured AI provider
3. Each step receives the accumulated context from all prior steps
4. Progress streams via SSE with step-by-step status indicators
5. Complete enrichment profile is saved to SQLite

By default the app uses local Claude CLI. Set `GTM_AI_PROVIDER` to `openai`, `anthropic`, or `command` to use another provider.

Pipeline steps:
1. **Web Research** — Company overview, product, leadership, recent news
2. **Tech Stack Detection** — Languages, frameworks, infrastructure, sales tools
3. **Funding & Growth Signals** — Funding rounds, hiring velocity, growth indicators
4. **Competitive Landscape** — Direct/adjacent competitors, market positioning

## Example Output

```json
{
  "web_research": {
    "product_description": "Cloud-based observability platform for DevOps teams",
    "target_market": "Mid-market to enterprise engineering organizations",
    "company_size": "500-1000 employees",
    "leadership": [{"name": "Jane Smith", "title": "CEO"}]
  },
  "tech_stack": {
    "languages": ["Go", "TypeScript", "Python"],
    "frameworks": ["React", "gRPC"],
    "infrastructure": ["AWS", "Kubernetes"],
    "confidence": "high"
  },
  "funding_signals": {
    "total_raised": "$180M",
    "funding_rounds": [{"round": "Series C", "amount": "$100M", "date": "2024-03"}]
  },
  "competitive_landscape": {
    "direct_competitors": [{"name": "Datadog", "overlap": "Full observability"}],
    "market_position": "Challenger"
  }
}
```

## Business Impact

Replaces manual multi-tool enrichment workflows (30+ minutes per account) with a single automated pipeline — produces a comprehensive company profile in under 3 minutes.
