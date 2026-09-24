"""Deterministic scoring helpers for speaking practice.

The browser supplies a German speech transcript and lightweight acoustic
features collected while recording.  Keeping the numeric scoring local makes
the feature usable even when the configured LLM is unavailable; the LLM is
only used to turn these measurements into personalised feedback.
"""

from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
import math
import re
import unicodedata


_WORD_RE = re.compile(r"[a-z0-9äöüß]+", re.IGNORECASE)


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def normalize_german(text: str | None) -> str:
    """Normalize German text without discarding umlauts or ß."""
    normalized = unicodedata.normalize("NFKC", text or "").casefold()
    return " ".join(_WORD_RE.findall(normalized))


def _tokens(text: str | None) -> list[str]:
    normalized = normalize_german(text)
    return normalized.split() if normalized else []


def _word_distance(reference: list[str], spoken: list[str]) -> int:
    """Return Levenshtein distance for word sequences."""
    if not reference:
        return len(spoken)
    previous = list(range(len(spoken) + 1))
    for row, ref_word in enumerate(reference, start=1):
        current = [row]
        for column, spoken_word in enumerate(spoken, start=1):
            current.append(
                min(
                    current[column - 1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (ref_word != spoken_word),
                )
            )
        previous = current
    return previous[-1]


def calculate_speaking_scores(
    reference_text: str,
    transcript: str,
    duration_seconds: float,
    pause_count: int = 0,
    intonation_variation: float = 0.0,
) -> dict[str, object]:
    """Score transcript accuracy, pace, pauses and vocal variation.

    ``intonation_variation`` is the coefficient of variation of RMS volume
    samples captured by the browser.  It is not a phonetic model, but it gives
    a stable rhythm/intonation signal and is clearly surfaced as such in the UI.
    """
    reference = _tokens(reference_text)
    spoken = _tokens(transcript)
    safe_duration = max(0.1, float(duration_seconds or 0.0))
    safe_pause_count = max(0, int(pause_count or 0))
    safe_variation = max(0.0, float(intonation_variation or 0.0))

    if not reference or not spoken:
        return {
            "totalScore": 0,
            "pronunciationScore": 0,
            "fluencyScore": 0,
            "intonationScore": 0,
            "accuracyScore": 0,
            "wordsPerMinute": round(len(spoken) * 60 / safe_duration, 1),
            "missingWords": reference[:8],
        }

    word_error_rate = _word_distance(reference, spoken) / max(1, len(reference))
    word_accuracy = _clamp((1.0 - word_error_rate) * 100)
    character_similarity = SequenceMatcher(
        None,
        normalize_german(reference_text),
        normalize_german(transcript),
    ).ratio() * 100

    reference_counts = Counter(reference)
    spoken_counts = Counter(spoken)
    matched_words = sum((reference_counts & spoken_counts).values())
    coverage = matched_words / max(1, len(reference))
    pronunciation = _clamp(
        word_accuracy * 0.55 + character_similarity * 0.25 + coverage * 100 * 0.20
    )

    words_per_minute = len(spoken) * 60 / safe_duration
    target_wpm = 105.0
    pace_score = _clamp(100 - abs(math.log(max(words_per_minute, 1) / target_wpm)) * 62)
    expected_pauses = max(1, round(safe_duration / 14))
    pause_penalty = max(0, safe_pause_count - expected_pauses) * 5
    completeness = _clamp(len(spoken) / max(1, len(reference)) * 100)
    fluency = _clamp(pace_score * 0.65 + completeness * 0.35 - pause_penalty)

    # Natural connected speech generally has some volume movement but should
    # not oscillate wildly.  Missing acoustic data receives a neutral score.
    if safe_variation <= 0:
        intonation = 65.0
    else:
        intonation = _clamp(100 - abs(safe_variation - 0.24) * 190, 35, 100)

    total = pronunciation * 0.50 + fluency * 0.30 + intonation * 0.20
    missing_words = list((reference_counts - spoken_counts).elements())[:8]

    return {
        "totalScore": round(total),
        "pronunciationScore": round(pronunciation),
        "fluencyScore": round(fluency),
        "intonationScore": round(intonation),
        "accuracyScore": round(word_accuracy),
        "wordsPerMinute": round(words_per_minute, 1),
        "missingWords": missing_words,
    }


def fallback_feedback(scores: dict[str, object]) -> dict[str, str]:
    pronunciation = int(scores.get("pronunciationScore") or 0)
    fluency = int(scores.get("fluencyScore") or 0)
    intonation = int(scores.get("intonationScore") or 0)
    weakest = min(
        (("发音准确度", pronunciation), ("流利度", fluency), ("语调节奏", intonation)),
        key=lambda item: item[1],
    )[0]
    missing_words = scores.get("missingWords") or []
    missing_hint = f" 重点核对：{', '.join(str(word) for word in missing_words[:5])}。" if missing_words else ""
    return {
        "analysis": (
            f"本次朗读的发音准确度为 {pronunciation} 分、流利度为 {fluency} 分、"
            f"语调节奏为 {intonation} 分；当前最需要加强的是{weakest}。{missing_hint}"
        ),
        "suggestion": "先以 0.8 倍速逐句跟读，再按正常速度完整朗读；录音后对照转写文本检查漏词和词尾。",
    }
