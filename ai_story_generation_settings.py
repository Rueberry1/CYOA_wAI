from __future__ import annotations

import json
import os
from typing import Any


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")


DEFAULT_SETTINGS: dict[str, Any] = {
    "passage_length": "800_words",  # 200_words, 400_words, 600_words, 800_words, 1000_words, no_limit
    "temperature": 0.7,
    "allow_fourth_wall": False,
    "single_location_only": False,
    "allow_steamy_scenes": False,
    "profanity_level": "none",  # none, mild, allow
    "violence_gore_level": "low",  # low, medium, high
    "romance_focus": "off",  # off, low, medium, high
}


PASSAGE_TOKEN_LIMITS = {
    "200_words": 260,
    "400_words": 520,
    "600_words": 760,
    "800_words": 1000,
    "1000_words": 1300,
    "no_limit": 2000,
}

# partially done 

PASSAGE_INSTRUCTIONS = {
    "200_words": "150-200",
    "400_words": "300-400",
    "600_words": "500-600",
    "800_words": "700-800",
    "1000_words": "800-1000",
    "no_limit": "a reasonably substantial but not excessive number of",
}


def _sanitize_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Merge unknown/missing values into defaults and keep known keys only."""
    merged = dict(DEFAULT_SETTINGS)
    for key in DEFAULT_SETTINGS.keys():
        if key in data:
            merged[key] = data[key]
    return merged


def load_settings() -> dict[str, Any]:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    raw = json.loads(content)
                    if isinstance(raw, dict):
                        settings = _sanitize_settings(raw)
                        save_settings(settings)
                        return settings
        except (json.JSONDecodeError, OSError):
            pass

    settings = dict(DEFAULT_SETTINGS)
    save_settings(settings)
    return settings

def save_settings(settings: dict[str, Any]) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(_sanitize_settings(settings), f, indent=2)


def get_max_tokens(settings: dict[str, Any], fallback: int = 800) -> int:
    preset = settings.get("passage_length", DEFAULT_SETTINGS["passage_length"])
    return PASSAGE_TOKEN_LIMITS.get(preset, fallback)


def build_settings_prompt_constraints(settings: dict[str, Any]) -> list[dict[str, str]]:
    """
    Convert user settings into system prompt constraints.
    These are separated from genre and story-state prompts.
    """
    constraints: list[dict[str, str]] = []

    # Fourth-wall guidance
    if settings.get("allow_fourth_wall", False):
        constraints.append({"role": "system", "content": "You may occasionally break the fourth wall if it fits the tone."})
    else:
        constraints.append({"role": "system", "content": "Do not break the fourth wall. Never mention being an AI, prompts, or game mechanics directly to the player."})

    # Location constraint
    if settings.get("single_location_only", False):
        constraints.append({"role": "system", "content": "Keep the entire story constrained to one primary location. New scenes should remain in that same place."})

    # Steamy scenes
    if not settings.get("allow_steamy_scenes", False):
        constraints.append({"role": "system", "content": "Do not include explicit sexual or steamy scenes. Keep romantic content non-explicit."})

    # Profanity level
    profanity_level = str(settings.get("profanity_level", "none")).lower()
    if profanity_level == "none":
        constraints.append({"role": "system", "content": "Do not use profanity."})
    elif profanity_level == "mild":
        constraints.append({"role": "system", "content": "If profanity is used, keep it mild and infrequent."})
    else:
        constraints.append({"role": "system", "content": "Profanity is allowed when contextually appropriate."})

    # Violence / gore level
    gore_level = str(settings.get("violence_gore_level", "low")).lower()
    if gore_level == "low":
        constraints.append({"role": "system", "content": "Keep violence low-intensity and avoid graphic gore details."})
    elif gore_level == "medium":
        constraints.append({"role": "system", "content": "Allow moderate violence detail, but avoid prolonged graphic gore."})
    else:
        constraints.append({"role": "system", "content": "High-intensity violence and gore detail are allowed when contextually appropriate."})

    # Romance focus
    romance_focus = str(settings.get("romance_focus", "off")).lower()
    if romance_focus == "off":
        constraints.append({"role": "system", "content": "Do not focus the story on romance."})
    elif romance_focus == "low":
        constraints.append({"role": "system", "content": "Allow light romantic subplots, but keep them secondary to the main plot."})
    elif romance_focus == "medium":
        constraints.append({"role": "system", "content": "Romance can be a meaningful subplot and may influence character choices."})
    else:
        constraints.append({"role": "system", "content": "Romance can be a major focus, while still preserving the selected genre tones."})

    return constraints

def get_passage_instruction(settings: dict[str, Any]) -> str:
    passage_length = settings.get(
        "passage_length",
        DEFAULT_SETTINGS["passage_length"]
    )
    return PASSAGE_INSTRUCTIONS[passage_length]