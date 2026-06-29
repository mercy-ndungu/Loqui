"""
Local eloquence scoring using spaCy and NLTK (no external API calls).

Universal metric for presentations, improv, and random topic challenges.
"""

from __future__ import annotations

import logging
import re
import time
from collections import Counter
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

FILLER_SINGLE = frozenset({
    "um", "uh", "er", "ah", "like", "basically", "literally", "actually",
    "really", "very", "so", "well", "okay", "ok", "right", "just",
})

FILLER_PHRASES: tuple[str, ...] = (
    "you know",
    "i mean",
    "kind of",
    "sort of",
    "you see",
)

IDEAL_SENTENCE_MIN = 10
IDEAL_SENTENCE_MAX = 20
MAX_SENTENCE_WORDS = 45
MIN_FRAGMENT_WORDS = 3


class FillerWordsAnalysis(BaseModel):
    """Filler word breakdown."""

    count: int = Field(ge=0)
    words: list[str] = Field(default_factory=list, alias="list")
    improvement: str

    model_config = {"populate_by_name": True}


class EloquenceAnalysisResult(BaseModel):
    """Structured eloquence analysis returned by local scoring."""

    grammar_score: int = Field(ge=0, le=100)
    grammar_feedback: str
    vocabulary_score: int = Field(ge=0, le=100)
    vocabulary_feedback: str
    filler_words: FillerWordsAnalysis
    pacing_score: int = Field(ge=0, le=100)
    pacing_feedback: str
    overall_score: int = Field(ge=0, le=100)
    top_3_improvements: list[str]
    strengths: list[str]

    @field_validator("top_3_improvements")
    @classmethod
    def validate_improvements(cls, value: list[str]) -> list[str]:
        if not value:
            return ["Keep practicing to refine your delivery"]
        return value[:3]


@lru_cache(maxsize=1)
def _load_spacy_model():
    """Load spaCy English model once per process."""
    import spacy

    try:
        return spacy.load("en_core_web_sm")
    except OSError as exc:
        logger.error(
            "spaCy model en_core_web_sm not found. Run: python -m spacy download en_core_web_sm"
        )
        raise RuntimeError(
            "Language scoring model not installed. Run setup_language_scoring.sh"
        ) from exc


def _ensure_nltk() -> None:
    """Download minimal NLTK data if missing."""
    import nltk

    for resource in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)


def _normalize_text(transcription: str) -> str:
    text = transcription.strip()
    if not text:
        return ""
    return re.sub(r"\s+", " ", text)


def _extract_filler_hits(text: str) -> list[str]:
    """Find filler words and multi-word filler phrases."""
    lower = text.lower()
    hits: list[str] = []

    for phrase in FILLER_PHRASES:
        hits.extend([phrase] * lower.count(phrase))

    tokens = re.findall(r"[a-zA-Z']+", lower)
    for token in tokens:
        if token in FILLER_SINGLE:
            hits.append(token)

    return hits


def _score_grammar(doc) -> tuple[int, str]:
    """Score grammar clarity using spaCy parse heuristics (0–100)."""
    sentences = list(doc.sents)
    if not sentences:
        return 50, "Speech was too short to assess grammar. Try a longer practice take."

    score = 100.0
    issues: list[str] = []
    run_on = 0
    fragments = 0
    no_verb = 0

    for sent in sentences:
        words = [t for t in sent if not t.is_space]
        word_count = len([t for t in words if t.is_alpha])
        if word_count < MIN_FRAGMENT_WORDS:
            fragments += 1
            score -= 8
        if word_count > MAX_SENTENCE_WORDS:
            run_on += 1
            score -= 10
        has_verb = any(t.pos_ in {"VERB", "AUX"} for t in words)
        if word_count >= MIN_FRAGMENT_WORDS and not has_verb:
            no_verb += 1
            score -= 6

    if run_on:
        issues.append(f"{run_on} very long sentence(s) — break them up for clarity")
    if fragments:
        issues.append(f"{fragments} fragment(s) detected — use complete sentences")
    if no_verb:
        issues.append(f"{no_verb} sentence(s) lack a clear verb")

    final = int(max(0, min(100, score)))
    if not issues:
        feedback = "Grammar is clear. Sentences are well structured and easy to follow."
    else:
        feedback = " ".join(issues[:2]) + "."
    return final, feedback


def _score_vocabulary(doc) -> tuple[int, str]:
    """Score vocabulary richness via lexical diversity and word sophistication."""
    tokens = [t.text.lower() for t in doc if t.is_alpha and len(t.text) > 1]
    if not tokens:
        return 50, "Not enough words to assess vocabulary. Speak a bit more on your next take."

    unique = len(set(tokens))
    ttr = unique / len(tokens)
    long_words = sum(1 for t in tokens if len(t) >= 7)
    long_ratio = long_words / len(tokens)

    counts = Counter(tokens)
    repetition_penalty = sum((c - 2) for c in counts.values() if c > 2) * 3

    raw = (ttr * 70) + (long_ratio * 30) * 100 / max(long_ratio, 0.01)
    raw = min(100, ttr * 100 + long_ratio * 40) - repetition_penalty
    score = int(max(0, min(100, raw)))

    if score >= 80:
        feedback = "Strong vocabulary with good variety. You use precise, expressive word choices."
    elif score >= 65:
        feedback = "Good word choice. Try swapping repeated words for more specific alternatives."
    else:
        feedback = "Vocabulary is repetitive. Expand with richer, more varied terms."

    return score, feedback


def _score_filler(filler_hits: list[str], word_count: int) -> tuple[int, FillerWordsAnalysis]:
    """Score filler usage; return count-based analysis for API compatibility."""
    count = len(filler_hits)
    per_minute_factor = (count / max(word_count, 1)) * 100
    filler_score = max(0, 100 - int(count * 5 + per_minute_factor * 0.5))

    if count == 0:
        improvement = "Excellent — no filler words detected. Maintain purposeful pauses instead."
    elif count <= 3:
        improvement = "A few filler words appeared. Replace them with brief, confident pauses."
    else:
        improvement = (
            "Reduce filler words (um, uh, like, you know). Pause silently instead of filling space."
        )

    return filler_score, FillerWordsAnalysis(
        count=count,
        words=filler_hits[:20],
        improvement=improvement,
    )


def _score_pacing(doc, word_count: int) -> tuple[int, str, float]:
    """Score pacing from average sentence length (proxy for rhythm)."""
    sentences = list(doc.sents)
    if not sentences:
        return 70, "Pacing could not be measured. Record a fuller 1–2 minute take.", 0.0

    avg_len = word_count / len(sentences)

    if IDEAL_SENTENCE_MIN <= avg_len <= IDEAL_SENTENCE_MAX:
        score = 95
        feedback = "Pacing is strong. Sentences flow naturally at a comfortable rhythm."
    elif avg_len < IDEAL_SENTENCE_MIN:
        score = max(55, 100 - int((IDEAL_SENTENCE_MIN - avg_len) * 4))
        feedback = "Sentences are short and choppy. Link ideas with fuller phrases."
    else:
        score = max(55, 100 - int((avg_len - IDEAL_SENTENCE_MAX) * 3))
        feedback = "Sentences run long. Break them up so listeners can follow each point."

    return int(score), feedback, avg_len


def _top_improvements(
    grammar: int,
    vocabulary: int,
    filler_count: int,
    pacing: int,
) -> list[str]:
    """Build ranked improvement suggestions from weakest dimensions."""
    candidates: list[tuple[int, str]] = []

    if grammar < 80:
        candidates.append((100 - grammar, "Tighten grammar — use complete sentences with clear subjects and verbs"))
    if vocabulary < 75:
        candidates.append((100 - vocabulary, "Expand vocabulary — replace generic words with more precise language"))
    if filler_count > 3:
        candidates.append((filler_count * 10, "Cut filler words — practice silent pauses instead of um, like, or you know"))
    if pacing < 80:
        candidates.append((100 - pacing, "Improve pacing — vary sentence length for a smoother, more engaging rhythm"))

    if not candidates:
        return [
            "Polish transitions between ideas for even smoother flow",
            "Add one vivid example to make your message more memorable",
            "End with a clear, concise takeaway",
        ]

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in candidates[:3]]


def _strengths(overall: int, grammar: int, vocabulary: int, filler_count: int) -> list[str]:
    """Highlight positive aspects of the delivery."""
    strengths: list[str] = []
    if overall >= 85:
        strengths.append("Excellent overall eloquence")
    elif overall >= 70:
        strengths.append("Solid, confident delivery")
    else:
        strengths.append("Engaged, conversational tone")

    if grammar >= 80:
        strengths.append("Clear sentence structure")
    if vocabulary >= 75:
        strengths.append("Good word variety")
    if filler_count <= 2:
        strengths.append("Minimal filler words")

    return strengths[:3] if len(strengths) >= 2 else strengths + ["Keep building momentum with regular practice"]


def score_eloquence(transcription: str) -> EloquenceAnalysisResult:
    """
    Universal local eloquence scoring for all challenge types.

    Returns structured scores (0–100) for grammar, vocabulary, pacing, and
    filler analysis compatible with the existing Loqui feedback API.
    """
    start = time.perf_counter()
    text = _normalize_text(transcription)
    if not text:
        raise ValueError("Transcription is empty")

    _ensure_nltk()
    nlp = _load_spacy_model()
    doc = nlp(text)

    word_tokens = [t.text.lower() for t in doc if t.is_alpha]
    word_count = len(word_tokens)

    grammar_score, grammar_feedback = _score_grammar(doc)
    vocabulary_score, vocabulary_feedback = _score_vocabulary(doc)
    filler_hits = _extract_filler_hits(text)
    filler_score, filler_analysis = _score_filler(filler_hits, word_count)
    pacing_score, pacing_feedback, _avg = _score_pacing(doc, word_count)

    overall = int(
        round((grammar_score + vocabulary_score + filler_score + pacing_score) / 4)
    )
    overall = max(0, min(100, overall))

    result = EloquenceAnalysisResult(
        grammar_score=grammar_score,
        grammar_feedback=grammar_feedback,
        vocabulary_score=vocabulary_score,
        vocabulary_feedback=vocabulary_feedback,
        filler_words=filler_analysis,
        pacing_score=pacing_score,
        pacing_feedback=pacing_feedback,
        overall_score=overall,
        top_3_improvements=_top_improvements(
            grammar_score, vocabulary_score, filler_analysis.count, pacing_score
        ),
        strengths=_strengths(overall, grammar_score, vocabulary_score, filler_analysis.count),
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Local eloquence scoring complete overall=%s grammar=%s vocab=%s pacing=%s "
        "fillers=%s elapsed_ms=%.1f",
        overall,
        grammar_score,
        vocabulary_score,
        pacing_score,
        filler_analysis.count,
        elapsed_ms,
    )
    return result


def analyze_eloquence(transcription: str) -> EloquenceAnalysisResult | None:
    """Analyze transcription; returns None only on unexpected failure."""
    try:
        return score_eloquence(transcription)
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Local eloquence scoring failed: %s", exc)
        return None
