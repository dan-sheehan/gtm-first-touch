# GTM First Touch

A portable workflow pack for taking **one target account** from initial fit assessment to research, a first-touch email, and discovery preparation inside your existing AI environment.

**ICP Scorer → Enrichment → Outbound First Touch → Discovery Prep**

Use it in ChatGPT, Claude, Claude Code, Codex, or another assistant that can follow Markdown instructions. The core is one [self-contained workflow](gtm-first-touch/workflow.md). It needs no Flask, SQLite, local server, Python installation, model-provider integration, or project API keys.

## Start with a real account

1. Open [workflow.md](gtm-first-touch/workflow.md) and copy its entire contents into a new conversation.
2. Add a short description of what you sell, who it is for, what makes an account a good fit, and the target account's name and website if known. Include any research you already have. The workflow includes an intake form; separate templates are optional.
3. Say: **“Start ICP Scorer for this account.”** Review or correct the assessment.
4. Say **“Continue to Enrichment,” “Continue to Outbound First Touch,”** and **“Continue to Discovery Prep”** as you are ready.
5. Review the research and draft before using them. Nothing is sent automatically.

By default, the assistant works one stage at a time. To get a complete draft, say **“Run all four stages using this context.”** Missing essential input may still require a question. To keep your work, ask **“Give me the complete updated account brief.”** Paste that brief with the workflow into a new conversation to resume.

## Try the included example

Open the [Harbor Analytics walkthrough](gtm-first-touch/examples/harbor-analytics.md). Paste the workflow and the example's **Exercise input** into a conversation, then use its starter prompt. It requires no browsing. Compare your results with the **Worked outputs** afterward.

Harbor, its people, source notes, and business situation are fictional. The example uses a fixed scenario date and a revenue-intelligence seller. Your real workflow uses **your** offer and ICP. Different models can produce different reasonable assessments and wording.

## Choose how to use it

### ChatGPT

Paste the complete workflow and your account/seller context into a chat. Follow the four stage requests above. If browsing is available in your session, let the assistant research public sources; otherwise supply notes or excerpts. Attachments are convenient where supported, but pasting text is sufficient.

### Claude

Use the same workflow and stage requests in a Claude conversation. Paste your seller context and account notes, review each result, and carry the account brief forward. No Claude Code installation or special project setup is required.

### Claude Code

Open a local copy of this repository in Claude Code and ask:

```text
Read gtm-first-touch/workflow.md and follow it for one target account.
Start with ICP Scorer. Here is my seller and account context: ...
```

For optional skill access, run the following **from the repository root**. It copies the complete pack, including its relative references, into your personal skills directory and leaves an existing installation alone:

```sh
mkdir -p ~/.claude/skills
if [ -e ~/.claude/skills/gtm-first-touch ]; then
  echo "Already installed; review the existing copy before replacing it."
else
  cp -R gtm-first-touch ~/.claude/skills/gtm-first-touch
fi
```

Then invoke **`/gtm-first-touch`** with your seller and account context. If the skill does not appear, restart Claude Code. Project installations can instead use `.claude/skills/gtm-first-touch/`. See the [official Claude Code skill instructions](https://code.claude.com/docs/en/skills).

### Codex

Open this repository in Codex and use the same direct file-reading request shown above. For optional skill access, run this **from the repository root**:

```sh
mkdir -p ~/.agents/skills
if [ -e ~/.agents/skills/gtm-first-touch ]; then
  echo "Already installed; review the existing copy before replacing it."
else
  cp -R gtm-first-touch ~/.agents/skills/gtm-first-touch
fi
```

Then invoke **`$gtm-first-touch`** with your seller and account context. If the skill does not appear, restart Codex. Project installations can instead use `.agents/skills/gtm-first-touch/`. See the [official OpenAI skill instructions](https://learn.chatgpt.com/docs/build-skills).

Both optional installations use the **same `SKILL.md` and workflow**. There are no separate host implementations. Installed copies are snapshots: updates require reviewing and replacing your installed copy. Do not copy only `SKILL.md`; its workflow must travel with it. Direct file reading is always available without installation.

## What is in the pack

| File | Purpose |
| --- | --- |
| [workflow.md](gtm-first-touch/workflow.md) | The canonical instructions, intake, four stage prompts, output guidance, and account handoff. Sufficient on its own. |
| [SKILL.md](gtm-first-touch/SKILL.md) | Optional shared entrypoint for assistants that support skills. |
| [Seller context](gtm-first-touch/templates/seller-context.md) | Optional reusable description of your offer, ICP, and supported claims. |
| [Account brief](gtm-first-touch/templates/account-brief.md) | Optional Markdown record for one account and its four-stage progress. |
| [ICP rubric](gtm-first-touch/references/icp-rubric.md) | An illustrative technology-company rubric adapted from the prototype; use only if it fits your seller. |
| [Personas](gtm-first-touch/references/personas.md) | Example sales, RevOps, founder, and SDR perspectives to adapt. |
| [Harbor Analytics](gtm-first-touch/examples/harbor-analytics.md) | Fictional input and worked outputs for the whole workflow. |

For basic use, paste only the workflow and your context. Templates, references, files on disk, skill installation, and browsing are optional.

## Privacy and limitations

The pack runs in the assistant you choose. That environment's access, billing, retention, and privacy settings apply to information you paste, attach, or let it read. A local Markdown file can still be transmitted to a model when you ask an assistant to use it. This project does not provide a private processing boundary.

Use only account and seller material you are comfortable sharing with that environment. Keep real account work separate from the included fictional example. If saving work in this repository, use `accounts/`; it is excluded from normal Git adds. That ignore rule is not encryption, does not protect already tracked files, and does not apply to other repositories. Check their rules before saving or committing account data there.

Research can be incomplete, stale, or mistaken. Numerical scores are decision aids, not predictions of purchase intent. Model research and interpretation can vary between runs; this pack does **not** promise deterministic or repeatable scoring. It does not enforce stage transitions, validate claims automatically, synchronize files, or guarantee that a conversation remembers earlier context. Verify important facts and review outreach yourself.

**GTM First Touch** prioritizes portable instructions, flexible judgment, and a small workflow. **local-gtm** serves the distinct need for controlled state, stronger validation, and more deterministic workflow guarantees. This pack deliberately does not recreate that system.

## Prototype history

The earlier Flask application is preserved only in Git history at commit `6300b09e5eca83314cc3d04a662ca57a4a6fa40f`. To inspect its original README without changing your checkout:

```sh
git show 6300b09e5eca83314cc3d04a662ca57a4a6fa40f:README.md
```

The pack preserves the scoring ideas, research passes, persona library, signal-led outreach, Markdown handoffs, and Harbor discovery questions. It replaces the app's hardcoded seller with explicit seller context and connects discovery to the earlier stages. The servers, databases, provider adapters, browser UI, setup tools, and reseeding commands are no longer part of the active product. Removing those files does not delete any databases the prototype previously created in your home directory.

Licensed under the [MIT License](LICENSE).
