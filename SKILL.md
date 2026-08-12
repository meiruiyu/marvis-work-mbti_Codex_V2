---
name: marvis-work-mbti
description: Safely scan explicitly authorized local work files, derive anonymized evidence, score Marvis work MBTI, generate a bright 3:4 digital-clone report, and collect post-result validation feedback. Use when a user asks to generate, test, validate, or improve a Marvis 工作版 MBTI / 数字分身报告 from local files, folders, applications, or work habits.
---

# Marvis Work MBTI

Generate one evidence-backed work-personality report through four internal modules. Keep collection and scoring separated by `evidence.json` so scoring can change without rescanning.

## Inputs

Require explicit authorized roots. Accept optional application-data roots only when the user grants them. Never infer permission to scan the home directory, mail, messages, browser history, calendars, photos, or cloud drives.

## Workflow

1. Read `references/privacy-policy.md`. Show the scan scope and exclusions before collection.
2. Run `scripts/collect_evidence.py` with one or more explicit `--root` values. It outputs anonymized `evidence.json`; it must not retain source text, filenames, entities, or full paths.
3. Run `scripts/score_profile.py` with `references/scoring-v1.json`. Do not use psychological MBTI or feedback during scoring.
4. Run `scripts/build_report.py` to create `report.json` and one fixed 3:4 HTML report. Use the type token from `references/personality-types.json` and the matching `assets/personalities/<TYPE>.png`; do not invent another visual style.
5. Render the HTML to PNG when a browser renderer is available. Verify the full 3:4 canvas, text wrapping, evidence values, and character asset.
6. In beta mode only, ask for psychological MBTI and user ratings after the raw result exists. Run `scripts/collect_feedback.py`; never feed this label back into the current score.

## Commands

```bash
python scripts/collect_evidence.py --root /authorized/workspace --exclude /authorized/workspace/generated-output --output evidence.json
python scripts/score_profile.py --evidence evidence.json --config references/scoring-v1.json --output score.json
python scripts/build_report.py --evidence evidence.json --score score.json --types references/personality-types.json --output-dir output
python scripts/collect_feedback.py --score score.json --output feedback.json
```

For the public comparison campaign, replace the scoring command with:

```bash
python scripts/score_profile.py --mode campaign_compare --psychological-type ENFJ --evidence evidence.json --config references/scoring-v1.json --output score.json
```

`campaign_compare` starts from the supplied psychological type and permits at most two evidence-backed flips. Never use it for beta accuracy evaluation.

## Output Contract

- `evidence.json`: M metadata, W scoring metrics, G zero-weight research features, and privacy audit counts.
- `score.json`: four independent axes, confidence, coverage, metric contributions, raw work type, and scoring version.
- `report.json`: title, summary, three dynamic evidence slots, axis copy, type tokens, and provenance-safe display values.
- `feedback.json`: beta-only validation label and ratings, collected after scoring.

Write all runtime outputs to a directory outside this skill package, such as `../work-mbti-output/<run-id>/`. Add that output directory to the collector's `--exclude` list whenever it sits inside an authorized scan root. The output directory is user data, not part of the installable skill.

Read `references/evidence-schema.json` when changing collection, `references/scoring-v1.json` when changing weights, and `references/personality-types.json` when changing type copy or colors.

## Boundaries

- Keep raw source text transient. Discard the sampled first 200 characters immediately after local classification.
- Exclude sensitive categories before text sampling. Refuse requests to include chats, mail bodies, browser history, credentials, medical data, identity documents, contracts, or private photos.
- Treat missing metrics as missing; remove them from the denominator. Never convert missing capability into evidence for either side.
- Keep G features at scoring weight zero. Use them only for report quirks and later aggregate validation.
- Use absolute counts for evidence sufficiency and report facts, not for letter scoring. Score letters from recency-weighted, project-capped ratios.
- Generate a four-letter result even at low confidence for the campaign, but use honest copy such as “几乎对半” rather than “典型”.
- Do not recommend five skills in the report.
