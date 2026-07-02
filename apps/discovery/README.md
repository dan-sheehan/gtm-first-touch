# Discovery Call Prep

AI-powered pre-call research tool that generates structured Discovery Briefs combining company intelligence, prospect background, competitive landscape, and tailored discovery questions. Designed for the 15 minutes before a first call.

## GTM Workflow

Automates the pre-call enrichment workflow that top-performing AEs do manually — company research, prospect LinkedIn review, recent news scanning, and question preparation. Outputs a structured brief with signal detection (funding rounds, leadership changes, hiring surges) and competitive positioning to walk into every discovery call prepared.

## How It Works

1. User enters a company URL and optional prospect details (name, title, LinkedIn)
2. The configured AI provider researches the company and prospect
3. AI produces a structured Discovery Brief with company intel, prospect background, recent signals, competitive landscape, discovery questions, and talking points
4. Results stream to the browser via SSE and render into categorized sections
5. Briefs are saved to SQLite and exportable as markdown

By default the app uses local Claude CLI. Set `GTM_AI_PROVIDER` to `openai`, `anthropic`, or `command` to use another provider.

## Example Output

```json
{
  "company": {
    "name": "Acme Corp",
    "industry": "Developer Tools",
    "headcount_range": "50-200",
    "funding_stage": "Series B",
    "tech_stack_signals": ["React", "AWS", "Datadog"]
  },
  "recent_signals": [
    {
      "signal": "Raised $45M Series B led by a]6z",
      "type": "funding",
      "source": "TechCrunch",
      "date": "2024-01-10"
    }
  ],
  "discovery_questions": [
    {
      "question": "How are you handling observability as your engineering team scales post-Series B?",
      "rationale": "Datadog in stack + rapid hiring = potential pain point",
      "persona_angle": "VP Engineering cares about developer productivity"
    }
  ]
}
```

## Business Impact

Reduces pre-call research from 30+ minutes to under 3 minutes — surfaces signals and competitive context that turn generic discovery calls into informed conversations.
