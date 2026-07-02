# GTM First Touch

A local-first GTM workflow bundle for turning one target account into a scored, researched, persona-specific first touch and discovery plan.

This folder contains the recruiter-facing four-app version:

1. **ICP Scorer** - decide whether the account is worth pursuing.
2. **Enrichment** - gather account context, funding, hiring, tech stack, and competitive notes.
3. **Outbound Email** - generate first-touch outreach from public GTM signals.
4. **Discovery Call Prep** - prepare pain hypotheses and discovery questions.

## Quick Start

```bash
make install
make doctor
make start
```

Open `http://localhost:8000`. `make start` runs the hub in the foreground; leave it open while using the apps.

Seed the deterministic Harbor Analytics demo from a second terminal:

```bash
make reseed
```

Use `make seed` to seed only when no saved demo data exists. Use `make stop` when finished.

## Model Provider

Seeded Harbor data works without a model provider. Live enrichment, outbound generation, and discovery prep use `apps/ai_client.py`.

| Provider | Setup |
| --- | --- |
| `claude_cli` default | Install/authenticate Claude CLI. Optional: `GTM_AI_MODEL` or `CLAUDE_MODEL` |
| `openai` | `export GTM_AI_PROVIDER=openai`, plus `OPENAI_API_KEY` or `GTM_AI_API_KEY`, and `GTM_AI_MODEL` or `OPENAI_MODEL` |
| `anthropic` | `export GTM_AI_PROVIDER=anthropic`, plus `ANTHROPIC_API_KEY` or `GTM_AI_API_KEY`, and `GTM_AI_MODEL` or `ANTHROPIC_MODEL` |
| `command` | `export GTM_AI_PROVIDER=command` and `export GTM_AI_COMMAND="your-command"` |

Run `make doctor` after changing provider settings. The `command` provider reads the full prompt from stdin and must print the model response to stdout.

## Recruiter Path: One Real Account

Start with the seeded Harbor walkthrough, then try one real account:

1. Open **ICP Scorer** and score the account using industry, size, funding stage, tech fit, growth signals, and buying signals.
2. Open **Enrichment**. It reads recent saved ICP scores and preselects the latest account, so you can run enrichment without retyping the company name.
3. Open **Outbound Email**. It reads recent saved Enrichment rows, preselects the latest enriched account, fills the company URL/name, and suggests a sales/revenue prospect when Enrichment found one. The prompt carries the selected enrichment context forward and looks for GTM signals like funding, hiring, new sales leadership, RevOps gaps, pipeline visibility, sales process, discovery, and coaching pain.
4. Open **Discovery Call Prep** and use the same account/prospect to generate pain hypotheses, discovery questions, landmines, and a next step.

Expected flow:

```text
ICP Scorer -> Enrichment -> Outbound Email -> Discovery Call Prep
```

## Privacy And Scope

This is a local alpha, not hosted SaaS. The Flask apps run on your machine, and saved app data is stored in local SQLite databases under your home directory.

Local/private: seeded Harbor data, saved scores, saved enrichments, saved email sequences, and saved discovery prep rows.

Sent to the model provider during live use: the prompt, company/prospect fields you enter, and any public account context the app asks the provider to research or use. With `claude_cli`, the app enables Claude web tools for public research. Other providers receive the prompt through their API or command wrapper.

## How It Runs

- Python + Flask
- SQLite per app in the user's home directory
- Vanilla HTML/CSS/JS
- Gateway at `http://localhost:8000`
- No frontend build step

## Useful Commands

```bash
make install      # install Python dependencies
make doctor       # check Python, packages, app files, ports, and provider setup
make start        # start all four apps plus the hub
make reseed       # reset Harbor Analytics demo data
make stop         # stop the local hub and app servers
make lint         # run ruff if installed
```
