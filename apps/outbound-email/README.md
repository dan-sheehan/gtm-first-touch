# Outbound Email Helper

Generates a first-touch outbound sequence from public account signals and a target prospect.

## GTM Workflow

The app researches a target account for signals such as funding, hiring, new sales leadership, RevOps gaps, growth pressure, pipeline visibility, sales process, discovery, and coaching pain. It then writes concise outreach from the user's company to the selected prospect.

## How It Works

1. Enter a company URL.
2. Optionally add prospect name, title, and department.
3. The configured AI provider researches public GTM signals and returns structured JSON.
4. The app saves the sequence locally and renders copy-ready email cards.

By default the app uses local Claude CLI. Set `GTM_AI_PROVIDER` to `openai`, `anthropic`, or `command` to use another provider.

## Example Output

```json
{
  "company_name": "Harbor Analytics",
  "account_signal_summary": "Harbor looks like a post-Series B sales scaling account with new sales leadership, active sales hiring, and no visible RevOps hire yet.",
  "emails": [
    {
      "type": "initial",
      "subject": "Scaling Harbor's sales team",
      "body": "Hi Priya,\n\nCongrats on joining Harbor..."
    }
  ]
}
```
