# Contributor roadmap validation — 2026-10-04

This delivery adds a fifth **Planned** view to the existing self-contained
architecture page. It changes contributor navigation and documentation, not
project runtime checks or coding-outcome evidence.

The final dataset contains **41 cards**: 3 Open milestone, 17 Planned research,
14 Conditional and 7 Proposed. There are 119 repository source references.
Each card has requirements, acceptance criteria and a small first contribution.
Conditional work retains its trigger; linked prerequisites reference existing
cards. The graph remains **107 nodes / 246 edges / 7 planes**, with the same
nodes and edges as commit `3528589c72b386363dfd17ea45aff2f47d63f388`.

## Actual checks

```powershell
.venv/Scripts/python.exe architecture/check.py --render
.venv/Scripts/python.exe -m py_compile architecture/check.py
git diff --check
```

The render command finished with `OK`. It regenerated the graph mirror and
exercised the actual Chromium page, including:

- Overview canvas, Data flow, Architecture and Workflow rendering.
- All 41 contributor cards and their native click/keyboard expansion.
- Full-card search, combined topic/status filtering and explained empty results.
- `#planned/<id>` entry links and prerequisite navigation to an already-current
  hash while its target is hidden by a filter.
- Keyboard focus on the revealed card's summary.
- Expanded-card retention on theme changes and the initial dark-to-light toggle.
- Computed light-theme text contrast of at least 4.5:1 for card badges and links.
- A 390px-wide contributor layout without horizontal content overflow.

Additional actual browser probes verified two simultaneously expanded cards,
their retention through filtering, linked prerequisite navigation and arrow,
Home and End navigation between tabs. Local desktop, expanded-card, light and
narrow screenshots were visually inspected. The updated Markdown source links
were checked locally with no missing targets.

The checker was observed failing before implementation with missing roadmap
data and a missing Planned tab. Read-only independent review then reproduced a
same-hash hidden-target navigation defect and insufficient light-theme text
contrast. Both are fixed and covered by the real browser check. Review also
identified the missing P26 lock-in commitment; it now has its own card, and all
published totals are reconciled. A second independent review ran the final
browser controls and found no remaining actionable issue.

## Boundaries

The source was published to `main` at
[`7ed9cac`](https://github.com/SatyamSingh-Git/ElevenPowers/commit/7ed9cac9d4eab14bc8a2b0b5763672d814c26edd).
The [GitHub Pages deployment](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/37185489468)
completed successfully. A fresh HTTPS read matched the committed HTML, and the
same real Chromium interaction check passed against the public URL for all five
tabs. The served HTML SHA-256 was
`6a2515c5c0657b2efeb0ef23bbd331efb9da89f44a43d6b8bc45acc795b03949`.
This deployment result is separate from the local checks above.

Model experiments, installed-host acceptance and representative runtime
overhead were not rerun for this page change. The current held-out coding-benefit
exit remains open; proposals in the view are contribution directions, not
implemented capabilities or approval to spend model capacity.

See [journey 59](../../journey/59-a-roadmap-contributors-can-open.md),
[the viewer guide](../../architecture/README.md) and
[the current roadmap](../../whats-offered/roadmap.md).
