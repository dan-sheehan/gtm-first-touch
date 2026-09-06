# Harbor Analytics — fictional walkthrough

This example demonstrates [the portable workflow](../workflow.md). **Harbor Analytics, the people, seller, source notes, and business relationships below are fictional.** Real tool names illustrate a possible stack; they do not establish a relationship with any real company. The `.example` address is an identifier, not a research source. Do not browse for Harbor or these people.

The fixed scenario date is **2026-07-01**. Dates and hiring counts describe that fictional moment, not today's market. These are illustrative outputs, not a benchmark or a promise of identical results.

## Exercise input

Paste this section, stopping before **Worked outputs**, after the complete workflow in a new conversation. The inputs include everything needed for the exercise; other pack files are optional.

### Seller context

- Seller: Example Revenue Studio; sender: Alex. Both are fictional.
- Offer: A revenue-intelligence working session and account-review framework that help sales managers turn account signals, call notes, and CRM context into clearer pipeline reviews and discovery coaching.
- Intended buyers: Sales leaders at growing B2B software companies.
- ICP: Software businesses with 51–200 employees, an expanding sales team, and an interest in improving account review. Interest must be tested; funding and hiring alone do not establish it.
- Exclusions: Organizations without a sales team or without a need for manager-led account review. Neither exclusion is established by the supplied notes.
- Supported capabilities: Mapping the current review process and sharing an account-review worksheet. No quantified results, customer references, software integrations, or automated capabilities are supplied.
- Desired invitation: A 15-minute exploratory conversation. A 20-minute working session is a possible later step if a relevant problem is confirmed.
- Tone: Brief, practical, curious.

### Account and evidence

Target: **Harbor Analytics**, `https://harboranalytics.example`. Prospect: **Priya Shah, VP of Sales**.

The following fictional notes are the only account evidence. They are **supplied scenario information, not independently verified public facts**. Treat the labels as references inside this exercise, not URLs or quotations from real documents. No live research has been performed.

| Note | Fictional date / coverage | Supplied information |
| --- | --- | --- |
| H1 — Company overview | 2026-07-01 snapshot | Harbor is a Boston-based B2B SaaS company with about 140 employees. Its retail data platform unifies store, e-commerce, inventory, and customer data for mid-market retail teams. Its technology includes Python, TypeScript, SQL, React, dbt, AWS, Snowflake, and Looker. |
| H2 — Funding summary | Series A: 2023-04-01; Series B: 2025-09-01 | A $9M Series A followed by a $30M Series B, for $39M total raised. The Series B was ten months before the scenario date. The funding summary describes planned product and GTM expansion; it provides no current budget. |
| H3 — Leadership note | 2026-05-01 announcement | Priya Shah joined as VP of Sales to develop the mid-market sales motion. Other leaders named in the scenario are Maya Chen, CEO, and Leo Martinez, VP of Product. |
| H4 — Hiring snapshot | 2026-07-01 | Twelve open roles across AEs, SDRs, and frontline sales management; approximately 38% year-over-year company headcount growth. No RevOps vacancy appears in the supplied listing. The note does not identify who currently owns revenue operations or whether that team exists. |
| H5 — Operating-tools note | 2026-07-01 snapshot; adoption dates unknown | The scenario lists Salesforce, HubSpot, Outreach, and Gong. It does not say any was recently adopted, how well they work together, or whether the company is evaluating a purchase. |
| H6 — Market note | 2026-07-01 snapshot | Harbor positions around retail-specific revenue workflows. Alternatives in its buyers' market include general BI tools and retail analytics specialists. No named competitor evaluation, prospect quote, or seller-product evaluation is supplied. |

Unknown: Priya's priorities, pipeline quality, actual review process, RevOps ownership, buying intent, available budget, and any response to outreach. No message has been sent and no meeting has been booked.

### Selected exercise rubric

For this exercise, the user explicitly chooses the following options from the prototype-derived sample rubric after reviewing H1–H6. This supplies the scoring inputs; the model should explain their evidence and limits, not treat them as independently validated classifications.

| Dimension | Weight | Selected option | Option score |
| --- | ---: | --- | ---: |
| Industry fit | 25 | SaaS / software | 100 |
| Company size | 20 | 51–200 employees | 100 |
| Funding stage | 20 | Series B | 100 |
| Technology fit | 15 | Modern stack with relevant analytics tools | 100 |
| Growth signals | 10 | Strong hiring and recent funding | 100 |
| Buying signals | 10 | No buying signal found in the material reviewed | 15 |

Calculate `sum(weight × option score) / sum(weights)`. Grades: A at 80 or above; B at 60 to below 80; C at 40 to below 60; D below 40. Apply thresholds to the unrounded result and display one decimal place. Unknown required inputs would leave the total and grade pending.

“No buying signal found” refers only to this review of H1–H6. Buying intent remains unknown. The exercise treats funding ten months earlier and the supplied hiring snapshot as sufficient for its growth category; a different seller or interpretation may not.

### Starter prompt

```text
Use the GTM First Touch workflow with the fictional exercise input above.
Work from these supplied notes only; do not browse or send anything.
Start at ICP Scorer using the selected exercise rubric. Keep hypotheses
separate from the fictional facts and wait for me before the next stage.
```

Then request Enrichment, Outbound First Touch, and Discovery Prep in turn. To practice without numerical scoring, omit the selected rubric and ask for a qualitative assessment. To practice a complete run, explicitly request all four stages.

## Worked outputs

The sections below illustrate one reasonable result. They use only the exercise input and do not represent live model-provider tests. For a portable saved example, keep the seller context, account evidence, and rubric above together with these outputs; H1–H6 must travel with the brief.

### 1. ICP Scorer

**Assessment:** Strong illustrative fit for the seller's intended audience; actual interest in account review is unconfirmed. Recommend **research further**, focusing on Priya's priorities and current review process.

| Dimension | Evidence and interpretation | Weight × score / 100 |
| --- | --- | ---: |
| Industry fit | H1 describes a SaaS product sold to retail teams; classify the vendor as software, not as a retailer. | 25.0 |
| Company size | H1 supplies about 140 employees, within 51–200. | 20.0 |
| Funding stage | H2 supplies Series B. This does not establish budget. | 20.0 |
| Technology fit | H1 supplies a modern data stack and analytics tools; the selected category fits this fictional seller's example rubric. | 15.0 |
| Growth signals | H2 and H4 support the exercise's chosen interpretation of recent funding and strong hiring. | 10.0 |
| Buying signals | No relevant new adoption, inbound interest, content engagement, or evaluation appears in H1–H6. The user selected the limited “none found” option after reviewing them. | 1.5 |
| **Total** | **91.5 / 100 — A under the selected rubric** | **91.5** |

Calculation: `(25×100 + 20×100 + 20×100 + 15×100 + 10×100 + 10×15) / 100 = 91.5`.

This is a decision aid, not evidence of purchase readiness. Evidence confidence is limited to the supplied fictional scenario; no public verification occurred. A high numerical grade does not resolve interest, budget, or process need. Neither seller exclusion is established, but the actual need for manager-led account review remains to be tested.

**Why this differs from the old demo:** The prototype selected “other tech” and a “technology trigger,” yielding 84.5 before its integer rounding to 84. Here Harbor is explicitly SaaS, and its undated tools list does not support a new buying trigger. The declared inputs therefore produce 91.5. The higher total reflects rubric choices, not stronger evidence of buying intent.

**Handoff:** Same account and Priya; proceed to Enrichment to organize the supplied evidence and identify what a real research pass would need to verify.

### 2. Enrichment

**Access:** Supplied fictional notes only. No browsing performed. All H1–H6 information remains scenario information.

**Account profile:** Harbor sells a retail data platform to mid-market retail teams. It has about 140 employees and $39M total funding in this scenario. The September 2025 Series B, Priya's May 2026 appointment, and twelve open sales roles suggest a useful conversation about scaling the sales motion. They do not establish a problem or available budget. Sources: H1–H4.

**Relevant context:** H1 and H5 describe several analytics and sales tools. Their presence may make process and ownership questions useful; it does not establish tool sprawl, poor data, broken handoffs, or recent adoption. H6 describes Harbor's market alternatives, not alternatives Priya is evaluating for the seller's offer.

**Professional persona:** Priya's stated mandate is developing the mid-market sales motion (H3). Hiring, manager consistency, and pipeline reviews are plausible responsibilities to ask about. They are not confirmed priorities or personal pain points.

| Signal | Evidence / date | Possible relevance | Limit |
| --- | --- | --- | --- |
| Sales-team expansion | H4, 2026-07-01 | More new reps could increase the importance of a shared review process. | Open roles are not completed hires. |
| New VP of Sales | H3, 2026-05-01 | A useful moment to ask how the sales motion is being developed. | Priya's current priorities are unknown. |
| Series B expansion plans | H2, 2025-09-01 | Background for the growth story. | Funding is ten months old in the scenario, not proof of current urgency. |

**Hypotheses to test:** Managers may benefit from a shared account-review routine; discovery coaching may become more important as new reps ramp. H4's missing RevOps vacancy suggests asking about ownership, not claiming there is no owner.

**Fit update:** No new evidence was added, so the initial fit assessment and rubric calculation remain unchanged. The central gap is whether account review is an actual priority. In a real account, verify the company identity, current role, dated hiring evidence, and seller capabilities before using specific personalization.

**Proposed angle:** How Priya wants managers to review account quality while the sales team grows. This connects the seller's supplied framework to a plausible process question without diagnosing Harbor.

**Handoff:** Use the same seller, account, and Priya. The outreach may reference the hiring snapshot only as an exercise; real use would require checking the claim first.

### 3. Outbound First Touch

**Angle and evidence:** H3 and H4 connect Priya's role to sales expansion. The operating-process concern is a hypothesis. The value proposition comes from the fictional seller description, not from a fabricated success story.

**Unsent fictional draft — verify any corresponding real-world claims before use.**

**Subject:** Harbor's account reviews

```text
Hi Priya,

With 12 sales roles open, how are you thinking about account reviews as new reps join Harbor?

A shared review routine may help managers see where discovery or next steps need attention.

We help sales teams map that routine using account signals, call notes, and CRM context.

Worth comparing notes for 15 minutes?

Alex
```

**Review notes:** The role and twelve openings come from unverified fictional notes. The draft states no budget, RevOps absence, bad forecasting, or confirmed pain. It claims only the seller's supplied capability. No recipient email address is known or needed for drafting. Keep the evidence and caveats outside the email if adapting it.

**Handoff:** This is a draft, not a sent email. Prepare discovery around the same account-review question; do not assume Priya has read it or agreed to a meeting.

### 4. Discovery Prep

**Context:** Priya is the scenario's VP of Sales, developing a mid-market sales motion amid planned hiring. The useful uncertainty is how managers currently review accounts and coach discovery. Seller: Example Revenue Studio; offer: account-review working session and framework. No meeting or reply is recorded.

**Opening:** “As you develop Harbor's sales motion, how are you thinking about the way managers review account quality with reps?”

| Pain hypothesis | Basis | How to test or disconfirm it |
| --- | --- | --- |
| Managers may use different standards for account quality. | Planned hiring and a developing sales motion, H3–H4. | Ask how reviews work today. A shared, effective process would weaken the hypothesis. |
| New reps may need more consistent discovery coaching. | Open AE/SDR and manager roles, H4. | Ask how coaching is delivered and where it works well. An established ramp process may already solve this. |
| Review preparation may involve manual context gathering. | Several systems in H5; no process evidence. | Ask what preparation actually involves. Integrated or simple workflows would disconfirm the concern. |

| Discovery question | Rationale |
| --- | --- |
| What changed in the sales motion after the Series B? | Tests whether historical funding is relevant to present priorities. |
| How do you decide which accounts deserve rep time today? | Connects the ICP and account-review stages to an actual process. |
| What does a high-quality opportunity look like for Harbor? | Looks for shared qualification criteria without assuming they are absent. |
| How do managers prepare for account reviews, and who owns that process? | Establishes the workflow and RevOps ownership without inferring a gap. |
| How are new reps learning what good discovery sounds like? | Tests the coaching hypothesis and invites existing strengths. |
| Where, if anywhere, does review preparation take time away from coaching? | Explores impact without asserting a manual-work problem. |
| As hiring progresses, what would you most want to keep consistent? | Lets Priya identify a priority rather than accepting the seller's diagnosis. |
| What would make a follow-up working session useful, and who should join? | Tests interest, ownership, and conditions for a sensible next step. |

**Competitive considerations:** Ask which existing systems and internal routines already support reviews. If Salesforce, Gong, or Outreach come up, ask what works and whether anything still needs attention. Do not presume replacement is needed. Broader BI tools are part of Harbor's market context, not evidence that Priya is evaluating a competing sales solution.

**Proposed next step:** If Priya identifies a meaningful account-review problem, offer a 20-minute working session to map the current process and apply the seller's account-review worksheet. Otherwise, acknowledge that the existing approach may be sufficient.

### Handoff

- Completed: all four stages as worked example outputs.
- Seller, target, prospect, rubric, and H1–H6 evidence: supplied above; keep them with this handoff when copying it.
- Corrections preserved: SaaS classification; no invented technology-adoption trigger; no claim that RevOps is absent; market competitors kept distinct from seller alternatives.
- Review status: fictional exercise, not owner-approved account research or outreach.
- Still unknown: Priya's actual priorities, process, ownership, interest, and budget. No independent research, outreach, or meeting has occurred.
- Next action: review the example, or request the optional follow-ups using the same fictional brief. For a real account, start a separate brief with your own seller context and evidence.
