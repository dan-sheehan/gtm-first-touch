# GTM First Touch

A portable, flexible GTM workflow pack for taking **one target account** from fit assessment to research, a first-touch email, and discovery prep.

**ICP Scorer → Enrichment → Outbound First Touch → Discovery Prep**

The core is one self-contained Markdown workflow that runs in the assistant you choose. No installation is required.

## Quick start

1. Open [gtm-first-touch/workflow.md](gtm-first-touch/workflow.md).
2. Copy its entire contents into a new **ChatGPT or Claude** conversation.
3. Add seller context: what you sell, who it is for, and what makes an account a good fit. Add **one target account**: its name and website, if known.
4. Say: **“Start ICP Scorer.”**
5. Review each result, then say **“Continue to Enrichment,” “Continue to Outbound First Touch,”** and **“Continue to Discovery Prep”** as you are ready.

Review important facts and drafts before use. Nothing is sent automatically.

If browsing is available in your session, the assistant can research public sources; otherwise supply notes or excerpts. The workflow includes an intake form; separate templates are optional.

The assistant works one stage at a time by default. To request a full draft, say **“Run all four stages using this context.”** Missing essential input may still require a question.

To resume later, ask **“Give me the complete updated account brief.”** Paste that brief with the workflow into a new conversation.

## Try the included example

Open the [Harbor Analytics walkthrough](gtm-first-touch/examples/harbor-analytics.md). Paste the workflow and the example's **Exercise input** into a conversation, then use its starter prompt. It requires no browsing. Compare your results with the **Worked outputs** afterward.

Harbor, its people, seller, and source notes are fictional. The example uses a fixed scenario date and a sample seller; real work uses **your** offer and ICP. Assessments and wording can vary between models.

## What is in the pack

| File | Purpose |
| --- | --- |
| [workflow.md](gtm-first-touch/workflow.md) | The canonical instructions, intake, four stages, and account handoff. Sufficient on its own. |
| [SKILL.md](gtm-first-touch/SKILL.md) | Optional shared entrypoint for assistants that support skills. |
| [Seller context](gtm-first-touch/templates/seller-context.md) | Optional reusable description of your offer, ICP, and supported claims. |
| [Account brief](gtm-first-touch/templates/account-brief.md) | Optional Markdown record for one account and its four-stage progress. |
| [ICP rubric](gtm-first-touch/references/icp-rubric.md) | An illustrative technology-company rubric; use only if it fits your seller. |
| [Personas](gtm-first-touch/references/personas.md) | Example sales, RevOps, founder, and SDR perspectives to adapt. |
| [Harbor Analytics](gtm-first-touch/examples/harbor-analytics.md) | Fictional input and worked outputs for the whole workflow. |

For basic use, paste only the workflow and your context. Templates, references, files on disk, skill installation, and browsing are optional.

## Optional: Claude Code and Codex

Both hosts use the **same canonical `workflow.md` and shared `SKILL.md`**. The instructions below only change how you access the pack.

<details>
<summary>Direct file access and optional skill installation</summary>

Open a local copy of this repository in either host and ask:

```text
Read gtm-first-touch/workflow.md and follow it for one target account.
Start with ICP Scorer. Here is my seller and account context: ...
```

No skill installation is needed for direct file access. For optional skill access, use the commands below **from the repository root**. They copy the complete pack into your personal skills directory and leave an existing installation alone.

### Claude Code

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

```sh
mkdir -p ~/.agents/skills
if [ -e ~/.agents/skills/gtm-first-touch ]; then
  echo "Already installed; review the existing copy before replacing it."
else
  cp -R gtm-first-touch ~/.agents/skills/gtm-first-touch
fi
```

Then invoke **`$gtm-first-touch`** with your seller and account context. If the skill does not appear, restart Codex. Project installations can instead use `.agents/skills/gtm-first-touch/`. See the [official OpenAI skill instructions](https://learn.chatgpt.com/docs/build-skills).

Installed copies are snapshots; review and replace them to update. Copy the whole `gtm-first-touch/` directory so the workflow and relative references stay together.

</details>

## Privacy and limitations

The pack runs inside the assistant you choose. That assistant's privacy, retention, billing, and access rules apply. Information you paste, attach, or ask it to read, including local files, can be transmitted to a model.

Use only material you are comfortable sharing with that assistant. If saving real account work in this repository, use `accounts/`, which is Git-ignored, and review staged changes before committing. Keep real account data out of published files.

Research can be wrong, incomplete, or stale. Scoring is a decision aid, not a prediction of purchase intent, and is not deterministic or guaranteed to repeat across runs. The pack does not enforce stage transitions or validate claims automatically. Verify important facts and review drafts before use. Nothing is sent automatically.

## Related project

**GTM First Touch** is a portable, flexible workflow pack. **local-gtm** is a separate project focused on stronger state, validation, and deterministic guarantees.

## Prototype history

Earlier versions used a local Flask/SQLite application. The current version intentionally returns to the original portable workflow-pack design. The previous implementation remains available in Git history at `6300b09`.

Licensed under the [MIT License](LICENSE).
