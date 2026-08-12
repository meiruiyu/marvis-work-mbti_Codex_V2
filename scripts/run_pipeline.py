#!/usr/bin/env python3
"""Run the complete Marvis work-MBTI pipeline and verify every required product."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", required=True, help="Explicitly authorized work root; repeat as needed.")
    parser.add_argument("--exclude", action="append", default=[], help="Excluded path; repeat as needed.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--research-consent", choices=("yes", "no"), required=True)
    parser.add_argument("--participant-id", help="Optional anonymous campaign ID, never a real name or contact detail.")
    parser.add_argument("--max-docs", type=int, default=300)
    parser.add_argument("--mode", choices=("beta_blind", "campaign_compare"), default="beta_blind")
    parser.add_argument("--psychological-type")
    return parser.parse_args()


def run(command: list[str]):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        stage = Path(command[1]).stem if len(command) > 1 else command[0]
        raise SystemExit(f"Pipeline stopped at {stage}. Review the message above and retry with a broader authorized scope if evidence was insufficient.") from exc


def main():
    args = parse_args()
    skill_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir).expanduser().resolve()
    temp_dir = output_dir / "internal"
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    evidence = temp_dir / "evidence.json"
    score = temp_dir / "score.json"

    collect = [
        sys.executable, str(skill_root / "scripts" / "collect_evidence.py"),
        "--output", str(evidence), "--max-docs", str(args.max_docs),
    ]
    for root in args.root:
        collect.extend(["--root", root])
    excluded = list(args.exclude) + [str(output_dir)]
    for path in excluded:
        collect.extend(["--exclude", path])
    run(collect)

    scoring = [
        sys.executable, str(skill_root / "scripts" / "score_profile.py"),
        "--mode", args.mode,
        "--evidence", str(evidence),
        "--config", str(skill_root / "references" / "scoring-v1.json"),
        "--output", str(score),
    ]
    if args.psychological_type:
        scoring.extend(["--psychological-type", args.psychological_type])
    run(scoring)

    run([
        sys.executable, str(skill_root / "scripts" / "build_report.py"),
        "--evidence", str(evidence), "--score", str(score),
        "--types", str(skill_root / "references" / "personality-types.json"),
        "--output-dir", str(output_dir),
    ])

    dataset = [
        sys.executable, str(skill_root / "scripts" / "export_dataset.py"),
        "--evidence", str(evidence), "--score", str(score),
        "--config", str(skill_root / "references" / "scoring-v1.json"),
        "--output-dir", str(output_dir), "--research-consent", args.research_consent,
    ]
    if args.participant_id:
        dataset.extend(["--participant-id", args.participant_id])
    run(dataset)

    required = [
        output_dir / "report.png",
        output_dir / "report.json",
        output_dir / "data_collection.csv",
        output_dir / "evidence_table.csv",
        output_dir / "data_manifest.json",
        evidence,
        score,
    ]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise SystemExit("Pipeline incomplete; missing products: " + ", ".join(missing))
    result = json.loads(score.read_text(encoding="utf-8"))
    print(json.dumps({
        "status": "complete",
        "raw_work_type": result["raw_work_type"],
        "display_type": result["display_type"],
        "primary_product": str(output_dir / "report.png"),
        "research_products": [
            str(output_dir / "data_collection.csv"),
            str(output_dir / "evidence_table.csv"),
            str(output_dir / "data_manifest.json"),
        ],
        "internal_products": [str(evidence), str(score)],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
