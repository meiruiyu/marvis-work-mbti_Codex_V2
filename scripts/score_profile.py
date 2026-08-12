#!/usr/bin/env python3
"""Score four independent Marvis work-MBTI axes from evidence.json."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

VALID_TYPES = {a + b + c + d for a in "EI" for b in "SN" for c in "TF" for d in "JP"}
CONFIDENCE_ORDER = ["low", "medium", "high"]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=("beta_blind", "campaign_compare"), default="beta_blind")
    parser.add_argument("--psychological-type", help="Required only in campaign_compare mode.")
    return parser.parse_args()


def clamp(value, low, high):
    return max(low, min(high, value))


def cap_weights(weights: list[float], cap: float) -> list[float]:
    if not weights or sum(weights) <= 0:
        return weights
    normalized = [value / sum(weights) for value in weights]
    for _ in range(20):
        excess = sum(max(0.0, value - cap) for value in normalized)
        if excess < 1e-9:
            break
        normalized = [min(value, cap) for value in normalized]
        uncapped = [index for index, value in enumerate(normalized) if value < cap - 1e-9]
        if not uncapped:
            break
        base = sum(normalized[index] for index in uncapped)
        if base <= 0:
            share = excess / len(uncapped)
            for index in uncapped:
                normalized[index] += share
        else:
            for index in uncapped:
                normalized[index] += excess * normalized[index] / base
    # If fewer than three metrics are active, a 34% cap cannot sum to 100%.
    # Keep the uncovered mass neutral instead of allowing one weak metric to dominate.
    return normalized


def confidence_level(gap: float, coverage: float, sources: int, settings: dict) -> str:
    high = settings["high"]
    medium = settings["medium"]
    if gap >= high["minimum_gap"] and coverage >= high["minimum_coverage"] and sources >= high["minimum_sources"]:
        return "high"
    if gap >= medium["minimum_gap"] and coverage >= medium["minimum_coverage"] and sources >= medium["minimum_sources"]:
        return "medium"
    return "low"


def downgrade_confidence(level: str) -> str:
    return CONFIDENCE_ORDER[max(0, CONFIDENCE_ORDER.index(level) - 1)]


def window_tendency(item: dict, window: str, alpha: float, scale: float) -> float | None:
    values = item.get("windows", {}).get(window)
    if not values:
        return None
    left = float(values.get("left", 0))
    right = float(values.get("right", 0))
    if left + right <= 0:
        return None
    p = (left + alpha) / (left + right + 2 * alpha)
    return clamp((p - 0.5) / scale, -1, 1)


def main():
    args = parse_args()
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    psychological = args.psychological_type.upper() if args.psychological_type else None
    if args.mode == "campaign_compare" and psychological not in VALID_TYPES:
        raise SystemExit("campaign_compare requires --psychological-type with a valid four-letter MBTI.")
    if args.mode == "beta_blind" and psychological:
        raise SystemExit("Do not provide psychological MBTI in beta_blind mode; collect it after scoring.")
    alpha = float(config["formula"]["smoothing_alpha"])
    scale = float(config["formula"]["tendency_scale"])
    cap = float(config["formula"]["metric_effective_cap"])
    axes_out = {}
    letters = []
    unscorable_axes = []

    for axis_id, axis in config["axes"].items():
        active = []
        raw_weights = []
        total_nominal = sum(item["weight"] for item in axis["metrics"])
        coverage_numerator = 0.0
        for definition in axis["metrics"]:
            item = evidence["white_metrics"].get(definition["id"])
            if not item or item.get("status") == "missing":
                continue
            left = float(item.get("left", 0))
            right = float(item.get("right", 0))
            if left + right <= 0:
                continue
            reliability = clamp(float(item.get("reliability", definition["default_reliability"])), 0, 1)
            coverage = clamp(float(item.get("coverage", 0)), 0, 1)
            if reliability <= 0 or coverage <= 0:
                continue
            p = (left + alpha) / (left + right + 2 * alpha)
            tendency = clamp((p - 0.5) / scale, -1, 1)
            effective = float(definition["weight"]) * reliability * coverage
            coverage_numerator += float(definition["weight"]) * coverage
            raw_weights.append(effective)
            active.append({
                "id": definition["id"],
                "name": definition["name"],
                "nominal_weight": definition["weight"],
                "reliability": reliability,
                "coverage": coverage,
                "left_evidence": left,
                "right_evidence": right,
                "smoothed_left_ratio": round(p, 4),
                "tendency": round(tendency, 4),
                "source_lineage": item.get("source_lineage", [definition["lineage"]]),
                "display": item.get("display", {})
            })
        capped = cap_weights(raw_weights, cap)
        if not active:
            unscorable_axes.append(axis_id)
        direction = 0.0
        recent_direction = 0.0
        annual_direction = 0.0
        recent_window_weight = 0.0
        annual_window_weight = 0.0
        for item, weight in zip(active, capped):
            item["effective_weight"] = round(weight, 4)
            item["contribution"] = round(item["tendency"] * weight, 4)
            direction += item["tendency"] * weight
            source_metric = evidence["white_metrics"][item["id"]]
            recent = window_tendency(source_metric, "0_90", alpha, scale)
            annual = window_tendency(source_metric, "0_365", alpha, scale)
            if recent is not None:
                recent_direction += recent * weight
                recent_window_weight += weight
            if annual is not None:
                annual_direction += annual * weight
                annual_window_weight += weight
        direction = clamp(direction, -1, 1)
        left_score = round(50 + 50 * direction)
        right_score = 100 - left_score
        chosen = axis["left"] if left_score >= right_score else axis["right"]
        letters.append(chosen)
        gap = abs(left_score - right_score)
        axis_coverage = coverage_numerator / total_nominal if total_nominal else 0
        sources = len({lineage for item in active for lineage in item["source_lineage"]})
        confidence = confidence_level(gap, axis_coverage, sources, config["confidence"])
        stability = "unknown"
        if recent_window_weight > 0 and annual_window_weight > 0:
            recent_direction /= recent_window_weight
            annual_direction /= annual_window_weight
            if recent_direction * annual_direction < 0:
                stability = "direction_changed"
                if config["confidence"].get("stability_downgrade_when_recent_direction_differs"):
                    confidence = downgrade_confidence(confidence)
            else:
                stability = "stable"
        strength = "strong" if max(left_score, right_score) >= 75 else "clear" if max(left_score, right_score) >= 60 else "slight"
        axes_out[axis_id] = {
            "left_letter": axis["left"],
            "right_letter": axis["right"],
            "left_label": axis["left_label"],
            "right_label": axis["right_label"],
            "left_score": left_score,
            "right_score": right_score,
            "chosen_letter": chosen,
            "chosen_score": max(left_score, right_score),
            "gap": gap,
            "coverage": round(axis_coverage, 4),
            "independent_source_count": sources,
            "confidence": confidence,
            "strength": strength,
            "stability": stability,
            "metrics": sorted(active, key=lambda item: abs(item["contribution"]), reverse=True)
        }

    if unscorable_axes:
        raise SystemExit(
            "Insufficient evidence for axes: " + ", ".join(unscorable_axes)
            + ". Authorize a broader recent work scope and collect again."
        )

    raw_type = "".join(letters)
    display_letters = list(psychological) if args.mode == "campaign_compare" else list(raw_type)
    flips = []
    if args.mode == "campaign_compare":
        settings = config["campaign_compare"]
        candidates = []
        for index, axis_id in enumerate(("EI", "SN", "TF", "JP")):
            axis = axes_out[axis_id]
            if raw_type[index] == psychological[index]:
                continue
            if (
                axis["gap"] >= settings["minimum_gap_to_flip"]
                and axis["coverage"] >= settings["minimum_coverage_to_flip"]
                and axis["independent_source_count"] >= settings["minimum_sources_to_flip"]
            ):
                candidates.append((axis["gap"], index, axis_id))
        for _, index, axis_id in sorted(candidates, reverse=True)[: settings["maximum_flips"]]:
            display_letters[index] = raw_type[index]
            flips.append(axis_id)

    output = {
        "schema_version": "1.0.0",
        "scoring_version": config["version"],
        "evidence_schema_version": evidence["schema_version"],
        "raw_work_type": raw_type,
        "display_type": "".join(display_letters),
        "mode": args.mode,
        "axes": axes_out,
        "disabled_for_scoring": config["disabled_for_scoring"],
        "psychological_type_used": args.mode == "campaign_compare",
        "psychological_type": psychological,
        "flipped_axes": flips
    }
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output_path), "raw_work_type": output["raw_work_type"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
