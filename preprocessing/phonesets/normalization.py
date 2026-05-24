"""Dataset-facing phone normalization helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.types import Interval
from preprocessing.phonesets.maps import (
    ENGLISH_DATASET_PHONE_FOLD_MAPS,
    GTSINGER_JAPANESE_PHONE_FOLD_MAP,
    JAPANESE_DATASET_PHONE_FOLD_MAPS,
    MANDARIN_PHONE_FOLD_MAP,
    MANDARIN_ZERO_INITIAL_PAIR_FOLD_MAP,
)


@dataclass(frozen=True, slots=True)
class JapaneseLabNormalizationConfig:
    preserve_devoiced_vowels: bool = True


DEFAULT_JAPANESE_LAB_NORMALIZATION = JapaneseLabNormalizationConfig()


def normalize_japanese_lab_phone(
    label: str,
    *,
    config: JapaneseLabNormalizationConfig = DEFAULT_JAPANESE_LAB_NORMALIZATION,
) -> str:
    normalized = label.strip()
    if not normalized:
        return normalized
    if config.preserve_devoiced_vowels:
        return normalized
    if normalized == "I":
        return "i"
    if normalized == "U":
        return "u"
    return normalized


def normalize_english_dataset_phone(label: str, *, source_dataset: str) -> str:
    normalized = label.strip()
    if not normalized:
        return normalized
    return ENGLISH_DATASET_PHONE_FOLD_MAPS.get(source_dataset, {}).get(
        normalized, normalized
    )


def normalize_japanese_dataset_phone(
    label: str,
    *,
    source_dataset: str,
    config: JapaneseLabNormalizationConfig = DEFAULT_JAPANESE_LAB_NORMALIZATION,
) -> str:
    normalized = label.strip()
    if not normalized:
        return normalized
    normalized = JAPANESE_DATASET_PHONE_FOLD_MAPS.get(source_dataset, {}).get(
        normalized, normalized
    )
    return normalize_japanese_lab_phone(normalized, config=config)


def normalize_gtsinger_english_phone(label: str) -> str:
    normalized = label.strip()
    if not normalized:
        return normalized
    if normalized == "<AP>":
        return "AP"
    if normalized == "<SP>":
        return "SP"
    if normalized == "ou":
        return "ow"
    normalized = re.sub(r"\d+$", "", normalized)
    return normalized.lower()


def normalize_gtsinger_japanese_phone(
    label: str,
    *,
    config: JapaneseLabNormalizationConfig = DEFAULT_JAPANESE_LAB_NORMALIZATION,
) -> str:
    normalized = label.strip()
    if not normalized:
        return normalized
    if normalized in {"i̥", "ɨ̥", "ɯ̥"}:
        devoiced = "I" if normalized == "i̥" else "U"
        return normalize_japanese_lab_phone(devoiced, config=config)
    if normalized in {"ɨ", "ɨː", "ɯ"}:
        return "u"
    folded = GTSINGER_JAPANESE_PHONE_FOLD_MAP.get(normalized, normalized)
    return normalize_japanese_lab_phone(folded, config=config)


def normalize_gtsinger_chinese_phone(label: str) -> str:
    normalized = label.strip()
    if not normalized:
        return normalized
    return MANDARIN_PHONE_FOLD_MAP.get(normalized, normalized)


def normalize_mandarin_dataset_phone(
    label: str,
    *,
    source_dataset: str,
) -> str:
    normalized = label.strip()
    if not normalized:
        return normalized
    return MANDARIN_PHONE_FOLD_MAP.get(normalized, normalized)


def normalize_mandarin_phone_sequence(
    labels: tuple[str, ...],
    *,
    source_dataset: str,
) -> tuple[str, ...]:
    normalized = tuple(
        normalize_mandarin_dataset_phone(label, source_dataset=source_dataset)
        for label in labels
    )
    result: list[str] = []
    index = 0
    while index < len(normalized):
        current = normalized[index]
        if index + 1 < len(normalized):
            merged = MANDARIN_ZERO_INITIAL_PAIR_FOLD_MAP.get(
                (current, normalized[index + 1])
            )
            if merged is not None:
                result.append(merged)
                index += 2
                continue
        result.append(current)
        index += 1
    return tuple(result)


def normalize_mandarin_phone_sequence_with_durations(
    labels: tuple[str, ...],
    durations: tuple[float, ...],
    *,
    source_dataset: str,
) -> tuple[tuple[str, ...], tuple[float, ...]]:
    if len(labels) != len(durations):
        raise ValueError(
            f"duration count must match label count, got {len(labels)} labels and {len(durations)} durations"
        )
    normalized = tuple(
        normalize_mandarin_dataset_phone(label, source_dataset=source_dataset)
        for label in labels
    )
    merged_labels: list[str] = []
    merged_durations: list[float] = []
    index = 0
    while index < len(normalized):
        current = normalized[index]
        current_duration = durations[index]
        if index + 1 < len(normalized):
            merged = MANDARIN_ZERO_INITIAL_PAIR_FOLD_MAP.get(
                (current, normalized[index + 1])
            )
            if merged is not None:
                merged_labels.append(merged)
                merged_durations.append(current_duration + durations[index + 1])
                index += 2
                continue
        merged_labels.append(current)
        merged_durations.append(current_duration)
        index += 1
    return tuple(merged_labels), tuple(merged_durations)


def normalize_mandarin_phone_intervals(
    phone_intervals: tuple[Interval, ...],
    *,
    source_dataset: str,
) -> tuple[Interval, ...]:
    normalized = tuple(
        Interval(
            label=normalize_mandarin_dataset_phone(
                interval.label, source_dataset=source_dataset
            ),
            start_sec=interval.start_sec,
            end_sec=interval.end_sec,
        )
        for interval in phone_intervals
    )
    result: list[Interval] = []
    index = 0
    while index < len(normalized):
        current = normalized[index]
        if index + 1 < len(normalized):
            merged = MANDARIN_ZERO_INITIAL_PAIR_FOLD_MAP.get(
                (current.label, normalized[index + 1].label)
            )
            if merged is not None:
                result.append(
                    Interval(
                        label=merged,
                        start_sec=current.start_sec,
                        end_sec=normalized[index + 1].end_sec,
                    )
                )
                index += 2
                continue
        result.append(current)
        index += 1
    return tuple(result)


__all__ = [
    "DEFAULT_JAPANESE_LAB_NORMALIZATION",
    "JapaneseLabNormalizationConfig",
    "normalize_english_dataset_phone",
    "normalize_gtsinger_chinese_phone",
    "normalize_gtsinger_english_phone",
    "normalize_gtsinger_japanese_phone",
    "normalize_japanese_dataset_phone",
    "normalize_japanese_lab_phone",
    "normalize_mandarin_dataset_phone",
    "normalize_mandarin_phone_intervals",
    "normalize_mandarin_phone_sequence",
    "normalize_mandarin_phone_sequence_with_durations",
]
