#!/usr/bin/env python3
"""Collect beta feedback after raw scoring; never alter the current score."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VALID_TYPES = {a + b + c + d for a in "EI" for b in "SN" for c in "TF" for d in "JP"}


def ask_rating(prompt: str, optional: bool = False):
    while True:
        value = input(f"{prompt}（1-7{'，回车跳过' if optional else ''}）: ").strip()
        if optional and not value:
            return None
        if value.isdigit() and 1 <= int(value) <= 7:
            return int(value)
        print("请输入 1 到 7。")


def rating(value, prompt: str):
    if value is None:
        return ask_rating(prompt)
    if 1 <= value <= 7:
        return value
    raise SystemExit(f"{prompt} must be from 1 to 7.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--psychological-type")
    parser.add_argument("--psychological-type-source", choices=("known", "formal_test", "micro_questions"))
    for field in ("ei-fit", "sn-fit", "tf-fit", "jp-fit", "overall-fit", "evidence-accuracy", "quirk-fun", "privacy-comfort", "share-intent"):
        parser.add_argument(f"--{field}", type=int)
    parser.add_argument("--most-accurate-metric", default="")
    parser.add_argument("--least-accurate-metric", default="")
    parser.add_argument("--occupation-group", default="")
    parser.add_argument("--experience-band", default="")
    args = parser.parse_args()
    command_mode = args.psychological_type is not None
    score = json.loads(Path(args.score).read_text(encoding="utf-8"))
    raw = score["raw_work_type"]
    psychological = args.psychological_type.upper() if args.psychological_type else ""
    while psychological not in VALID_TYPES:
        psychological = input("你的传统心理 MBTI（例如 ENFJ）: ").strip().upper()
        if psychological not in VALID_TYPES:
            print("请输入有效的 4 字母 MBTI。")
    source = args.psychological_type_source
    if source is None and command_mode:
        raise SystemExit("--psychological-type-source is required with --psychological-type.")
    if source is None:
        source = input("获取方式 known / formal_test / micro_questions: ").strip()
        if source not in {"known", "formal_test", "micro_questions"}:
            source = "known"
    axis_fit = {
        "EI": rating(args.ei_fit, "EI 这一维像不像你的工作方式"),
        "SN": rating(args.sn_fit, "SN 这一维像不像你的工作方式"),
        "TF": rating(args.tf_fit, "TF 这一维像不像你的工作方式"),
        "JP": rating(args.jp_fit, "JP 这一维像不像你的工作方式"),
    }
    output = {
        "schema_version": "1.0.0",
        "raw_work_type": raw,
        "psychological_type": psychological,
        "psychological_type_source": source,
        "matched_letters": sum(a == b for a, b in zip(raw, psychological)),
        "axis_fit": axis_fit,
        "overall_fit": rating(args.overall_fit, "整体结果像不像你的工作方式"),
        "evidence_accuracy": rating(args.evidence_accuracy, "电脑证据准确吗"),
        "quirk_fun": rating(args.quirk_fun, "怪癖有趣吗"),
        "privacy_comfort": rating(args.privacy_comfort, "隐私体验是否舒适"),
        "share_intent": rating(args.share_intent, "你愿意分享这张报告吗"),
        "most_accurate_metric": args.most_accurate_metric if command_mode else input("最准的证据指标 ID（可留空）: ").strip(),
        "least_accurate_metric": args.least_accurate_metric if command_mode else input("最离谱的证据指标 ID（可留空）: ").strip(),
        "occupation_group": args.occupation_group if command_mode else input("职业大类（可留空）: ").strip(),
        "experience_band": args.experience_band if command_mode else input("工作年限区间（可留空）: ").strip()
    }
    target = Path(args.output).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), "matched_letters": output["matched_letters"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
