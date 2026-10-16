# Publication verification and release checklist

## Source-based review

- [x] M1–M5 Python implementation reviewed from supplied repository transcript.
- [x] Existing M4 evidence document reviewed (save, recall, versioned update, revocation, customer filtering).
- [x] L0 and L1 diagrams generated with logical **Shared Cortex Agent** label.
- [x] M5 independent SQL evaluator shown as a separate application path.
- [ ] M5 screenshots/SQL results **not supplied in this review**; locate and attach a concise evidence index before claiming end-to-end M5 validation in the public README.
- [ ] Verify active procedure version and threshold in live Snowflake before recording a current-state screenshot.
- [ ] Re-run a brief smoke test **only if desired**; prior M1–M4 evidence exists and should be reused.

## Local integration (no automatic edits performed)

1. Review `README_PUBLICATION_SECTION.md` and append it to your existing README (do not replace the M1/M2 sections).
2. Copy `docs/MEMORY_PATTERNS.md` and `docs/EVIDENCE_AND_RELEASE_CHECKLIST.md` to your repository `docs/`.
3. Copy the SVG and PNG files from `architecture/` to your repository `architecture/`.
4. Preserve the existing untracked files: `sql/p0_foundation/07_m5_register_procedure_v2.sql.bak` and `sql/p2_conversation_state/24_p2b_hybrid_registry_probe.sql`.
5. Confirm image rendering and links on GitHub; check for credentials and identifying customer information.
6. Stage **explicit paths only**, inspect `git diff --cached`, then commit after approval. No remote push is performed here.
7. Add the real GitHub repository URL to the LinkedIn post **only after the repository is publicly accessible**.

## Suggested read-only checks

```powershell
git status --short
git diff --check
git log -1 --oneline
```

## Suggested staging after integration and review

```powershell
git add README.md docs/MEMORY_PATTERNS.md docs/EVIDENCE_AND_RELEASE_CHECKLIST.md architecture/L0_linkedin_reference.svg architecture/L0_linkedin_reference.png architecture/L1_technical_reference.svg architecture/L1_technical_reference.png
git diff --cached --check
git diff --cached --stat
# After reviewing staged content:
# git commit -m "docs: publish agent memory reference architectures and guide"
```

**Important:** No live Snowflake execution, Git commit, remote push, or LinkedIn publication was performed in producing this package.
