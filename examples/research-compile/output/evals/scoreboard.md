**Verdict: PASS.** The compiled skill matches or beats running the originals.

| Measure | Run the originals | Compiled | Change |
| --- | --- | --- | --- |
| Static coverage (4 evals with needs) | 1.00 | 1.00 | +0.00 |
| Needs already in context on activation | 1.00 | 0.62 | -0.38 |
| Context on activation (est. tokens) | 36,038 (24 SKILL.md) | 2,123 (1 SKILL.md) | -33,915 |
| Listing (description characters) | 7,743 | 529 | -7,214 |
| Live tier | not run (pass --live with --max-cost-usd) | | |

| Eval | Needs | Originals | Compiled | Missing in the compiled skill |
| --- | --- | --- | --- | --- |
| company-brief | 3 | 3 | 3 |  |
| fact-check-one-pager | 2 | 2 | 2 |  |
| plain-market-summary | 3 | 3 | 3 |  |
| send-check | 2 | 2 | 2 |  |

Tolerance for sampled answers: 0.05. Static coverage has no tolerance.
