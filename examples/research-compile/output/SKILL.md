---
name: research-brief
description: "Research a company, market or product from public evidence and write a short brief where every number and claim carries its source: each claim tagged observed, inferred or unknown, a ledger of evidence, open questions left open, plain wording, and a reader test before it is sent. Also fact-checks an existing one-pager or deck claim by claim. Use when asked to research a company or competitor, build a sourced brief, back a claim with evidence, fact-check a market number, or prepare a brief that someone will repeat to others."
license: CC-BY-4.0 AND MIT. Each source folder holds its own LICENSE
---

# Research Brief

A brief is done when each conclusion says how you know it. This skill takes the evidence ledger from `reverse-engineer-evidence-research/`, the claim check from `reverse-engineer-claims-audit/`, plain wording from `work-humanizer-work-humanizer/`, the reader test from `bug-bounty-triage/`, and the analysis design step from `ai-analyst-workbench-ethan-analysis-brief/`. `MERGE.md` says what was left out and why.

**What wins, top first:**
1. The user's own words in the conversation
2. Honesty: every number and claim carries its source; a missing fact stays unknown, never a plausible guess
3. The three tags (observed, inferred, unknown) decide how a claim is written
4. The reader test before anything is sent
5. Plain claims for the wording
6. Taste

## How a brief is made

1. Write the questions first. With none given, use five: what they sell, who buys it, how big they are, what they run on, what they are doing now.
2. Before gathering, settle what each number means: its numerator, denominator, source and period, and whether both sides of a comparison use the same definition. (`ai-analyst-workbench-ethan-analysis-brief/` has this step in full, in Chinese.)
3. Gather from public sources: the company's own pages, filings, press, job posts. Read pages as text. Never run their scripts and never get around a login wall, paywall or bot block; mark that page unknown instead.
4. Tag every claim (below) and keep a ledger: the claim, its tag, the evidence (URL and date read), confidence, and the search boundary.
5. Close the loop: mark each question answered, partial or open. A requested question that is still open stays in the brief as open.
6. Word it plainly (below), then run the reader test.

To fact-check a document that already exists, follow the procedure in `reverse-engineer-claims-audit/REVERSE-ENGINEER-CLAIMS-AUDIT.md`: tag each claim by what stands behind it, rank by damage if wrong, check the top ones first. Its job table names one paid provider; any way of reading public pages does the same job.

## The three tags

- observed: a looot run or a public page returned it. Cite the run id or the URL and the date read.
- inferred: you concluded it from observed items. Name the items.
- unknown: no run answered it, or providers disagreed. Say what would settle it and the price.

Never write an inferred item as if it were observed. A provider that returns nothing has missed. That does not prove the thing does not exist. A third-party article is not first-party evidence. Write what it says as unknown, "reported by <source>".

## Output format

```
# <Company>: evidence brief (<date>)
Spent: $<actual> of $<cap>. Calls: <n>.

## Answers
1. <question>: <one-line answer>. [observed|inferred|unknown, confidence]

## Ledger
| # | Claim | Tag | Evidence | Confidence | Boundary |

## Open questions
- <question>: would cost $<x> via <job>. Worth it? yes or no
```

## Plain claims (from work-humanizer, part C of its tells)

- **An adjective with no specific behind it** ("significant", "seamless", "powerful", "robust", "game-changing"). Attach the number, name, or mechanism the source gives, or cut the adjective. Never supply a number the source lacks.
- **Inflated significance.** "a pivotal moment", "a testament to", "reshaping the landscape", "the future looks bright". Keep the fact, drop the significance.
- **Marketing register outside marketing**, and stock AI vocabulary. Lists in `work-humanizer-work-humanizer/tells.md`. One hit is weak; several together are the tell.
- **Constructions nobody says out loud.** "The recommended approach is X" becomes "Do X". "Serves as" becomes "is". Nominalizations ("perform an evaluation of") become verbs. Op-ed verbs for sources ("posits", "contends", "asserts") become "says" or "writes". The test: would you say this sentence to a smart friend over coffee? If you'd say something plainer, write that.
- **Vague authority.** "Experts agree", "studies show", "many companies". Name who, if the source does. Otherwise cut or scope it ("in our tests").

## Before you send: the reader test

Adapted from bug-bounty-triage's knowledge-assumption audit and its report rules 2 and 9, for a brief instead of a security report.

Read only the brief, as a capable reader who has never seen the target. Do not send it while any answer is no:

- Can the reader find the source of every number and every claim from the brief alone, without asking you?
- Is every inference marked as an inference, and every unknown left as unknown rather than smoothed over?
- Does each conclusion name the observed items it rests on?
- Can the reader tell a fact from the source's own words apart from your summary of it?
- Has repeated explanation been cut while every non-obvious detail stays?

If the evidence you have cannot answer a question the brief claims to answer, do not pad it with prose. Mark the question open and say what would settle it.

## Where the rest is

Read these only when a step above sends you to them.

- `ai-analyst-workbench-ethan-analysis-brief/`: 2 files from Ethanyang9512/ai-analyst-workbench. `ai-analyst-workbench-ethan-analysis-brief/AI-ANALYST-WORKBENCH-ETHAN-ANALYSIS-BRIEF.md` is its original SKILL.md, with "第二步：取数之前攻一遍分析设计", "交付规范", "交付前".
  - `ai-analyst-workbench-ethan-analysis-brief/assets/` (1): `brief-template.md`
- `reverse-engineer-claims-audit/`: 1 files from loootai/reverse-engineer. `reverse-engineer-claims-audit/REVERSE-ENGINEER-CLAIMS-AUDIT.md` is its original SKILL.md, with "Claims audit", "Inputs", "Procedure", "Jobs (catalog revision 101897, read 2026-10-11; inspect shows the live price)", "Output format", "Example", "Related".
- `reverse-engineer-evidence-research/`: 1 files from loootai/reverse-engineer. `reverse-engineer-evidence-research/REVERSE-ENGINEER-EVIDENCE-RESEARCH.md` is its original SKILL.md, with "Evidence research", "Inputs", "Procedure", "Jobs (catalog revision 101897, read 2026-10-11; inspect shows the live price)", "Example", "Related".
- `bug-bounty-triage/`: 4 files from Sequester-AG/bug-bounty-triage. `bug-bounty-triage/BUG-BOUNTY-TRIAGE.md` is its original SKILL.md, with "REPORT AUDIENCE AND INFORMATION DENSITY", "SOURCE FIDELITY, NEVER REDACT", "PHASE 2: LIVE END-TO-END TESTING (WHEN APPLICABLE AND AUTHORIZED)", "PHASE 3: SUBMISSION READINESS", "PHASE 4: ESCALATION (MAXIMIZE BOUNTY)", "PHASE 5: GENERATE SUBMISSION REPORT", "PHASE 6: TRIAGE DECISION", "RULES".
- `work-humanizer-work-humanizer/`: 3 files from phuryn/work-humanizer. `work-humanizer-work-humanizer/WORK-HUMANIZER-WORK-HUMANIZER.md` is its original SKILL.md, with "work-humanizer", "Pick the mode", "Interview mode", "Rewrite mode", "Sound like a person, not a costume", "Keep what is already human", "Genre notes", "Final checks (every time)" and 1 more sections.

## Sources

- `ai-analyst-workbench-ethan-analysis-brief/`: Ethanyang9512/ai-analyst-workbench @ 2b5d00b (2026-10-22), CC-BY-4.0, copied. `ai-analyst-workbench-ethan-analysis-brief/README.md` says what was kept and why.
- `reverse-engineer-claims-audit/`: loootai/reverse-engineer @ 4aa911d (2026-10-11), MIT, copied. `reverse-engineer-claims-audit/README.md` says what was kept and why.
- `reverse-engineer-evidence-research/`: loootai/reverse-engineer @ 4aa911d (2026-10-11), MIT, copied. `reverse-engineer-evidence-research/README.md` says what was kept and why.
- `bug-bounty-triage/`: Sequester-AG/bug-bounty-triage @ 9684e1b (2026-10-09), MIT, copied. `bug-bounty-triage/README.md` says what was kept and why.
- `work-humanizer-work-humanizer/`: phuryn/work-humanizer @ 0a90657 (2026-10-10), MIT, copied. `work-humanizer-work-humanizer/README.md` says what was kept and why.
