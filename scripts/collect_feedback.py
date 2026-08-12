#!/usr/bin/env python3
"""Collect beta feedback after raw scoring; never alter the current score."""

from __future__ import annotations

import argparse
import json
import re
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    score = json.loads(Path(args.score).read_text(encoding="utf-8"))
    raw = score["raw_work_type"]
    while True:
        psychological = input("你的传统心理 MBTI（例如 ENFJ）: ").strip().upper()
        if psychological in VALID_TYPES:
            break
        print("请输入有效的 4 字母 MBTI。")
    source = input("获取方式 known / formal_test / micro_questions: ").strip()
    if source not in {"known", "formal_test", "micro_questions"}:
        source = "known"
    axis_fit = {axis: ask_rating(f"{axis} 这一维像不像你的工作方式") for axis in ("EI", "SN", "TF", "JP")}
    output = {
        "schema_version": "1.0.0",
        "raw_work_type": raw,
        "psychological_type": psychological,
        "psychological_type_source": source,
        "matched_letters": sum(a == b for a, b in zip(raw, psychological)),
        "axis_fit": axis_fit,
        "overall_fit": ask_rating("整体结果像不像你的工作方式"),
        "evidence_accuracy": ask_rating("电脑证据准确吗"),
        "quirk_fun": ask_rating("怪癖有趣吗"),
        "privacy_comfort": ask_rating("隐私体验是否舒适"),
        "share_intent": ask_rating("你愿意分享这张报告吗"),
        "most_accurate_metric": input("最准的证据指标 ID（可留空）: ").strip(),
        "least_accurate_metric": input("最离谱的证据指标 ID（可留空）: ").strip(),
        "occupation_group": input("职业大类（可留空）: ").strip(),
        "experience_band": input("工作年限区间（可留空）: ").strip()
    }
    target = Path(args.output).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), "matched_letters": output["matched_letters"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
