from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from typing import Any

from openai import OpenAI

from ai_story_generation_genres import BASE_PROMPTS, build_genre_prompts
from ai_story_generation_settings import build_settings_prompt_constraints, get_max_tokens


# === Checkpoints (currently global; later can be made genre-aware) ===
CHECKPOINTS = {
    4: "Something unexpected or mysterious happens that shifts the player's understanding of their journey or surroundings and leads them to have a long term goal.",
    18: "The player encounters a new world, culture, or phenomenon that challenges previous assumptions and offers new possibilities.",
    27: "A situation arises where the player must make a difficult ethical or strategic choice, with no clearly right answer.",
    40: "The consequences of earlier choices start to ripple out, changing available resources, allies, or goals in significant ways.",
    55: "The player is presented with an opportunity or temptation that could lead their story in a radically new direction, if they choose to pursue it.",
    80: "A personal loss or sacrifice tests the player's resolve and ambitions.",
    100: "The story should now move toward a satisfying ending or resolution within the next few scenes.",
}


# === API Setup ===
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# === Cache Setup ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(SCRIPT_DIR, "story_cache.json")

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r") as f:
            content = f.read().strip()
            story_cache: dict[str, Any] = json.loads(content) if content else {}
    except (json.JSONDecodeError, OSError):
        story_cache = {}
else:
    story_cache = {}


def save_cache() -> None:
    with open(CACHE_FILE, "w") as f:
        json.dump(story_cache, f, indent=2)


def clear_cache() -> None:
    story_cache.clear()
    save_cache()


def get_path_hash(seed: int, path_choices: list[str], genre_key: str | None = None) -> str:
    """
    Generate a deterministic hash for a sequence of choices under a given seed.
    If genre_key is provided, include it so the same seed+path under different
    genres creates distinct stories. If genre_key is None, fall back to the
    legacy format for backwards compatibility with existing cache entries.
    """
    if genre_key is None:
        path_string = f"{seed}:{'|'.join(path_choices)}"
    else:
        path_string = f"{seed}:{genre_key}:{'|'.join(path_choices)}"
    return hashlib.sha256(path_string.encode()).hexdigest()


def get_checkpoint_instruction(choice_count: int) -> str | None:
    """Return a checkpoint directive if we are near or past a milestone."""
    if choice_count == 0:
        return None
    for checkpoint, instruction in sorted(CHECKPOINTS.items()):
        if choice_count >= checkpoint and choice_count < checkpoint + 3:
            return instruction
    return None


def clamp(val: int, minv: int, maxv: int) -> int:
    return max(minv, min(maxv, val))


def extract_choices(segment: str) -> list[str]:
    lines = segment.splitlines()
    options: list[str] = []
    pattern = re.compile(r"^\s*\d+[.)]\s+.+")
    for line in lines:
        if pattern.match(line.strip()):
            if "choose" in line.lower() or "choice" in line.lower():
                continue
            options.append(line.strip())
    # preserve order, remove duplicates
    return list(dict.fromkeys(options))


def extract_stats_update(segment: str) -> dict[str, Any] | None:
    match = re.search(r"STATS_UPDATE:\s*({.*?})", segment)
    if match:
        try:
            stats = ast.literal_eval(match.group(1))
            result = {
                "morality": int(stats.get("morality", 0)),
                "AstraCore Dynamics": int(stats.get("AstraCore Dynamics", 0)),
                "Stellar Concorde Collective": int(stats.get("Stellar Concorde Collective", 0)),
                "major": stats.get("major", None),
            }
            return result
        except Exception:
            return None
    return None


def extract_npcs_update(segment: str) -> dict[str, Any] | None:
    match = re.search(r"NPCS_UPDATE:\s*({.*?})", segment)
    if match:
        try:
            data = ast.literal_eval(match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            return None
    return None

def extract_events(segment: str) -> list[dict[str, Any]]:
    match = re.search(r"EVENTS_UPDATE:\s*(\[.*?\])", segment, re.DOTALL)

    if not match:
        return []

    try:
        data = ast.literal_eval(match.group(1))

        if isinstance(data, list):
            return [
                event
                for event in data
                if isinstance(event, dict)
            ]

    except Exception:
        return []

    return []

def generate_story_segment(
    seed: int,
    player_choices: dict[str, Any],
    path_choices: list[str],
    npc_states: dict[str, Any],
    game_state: dict[str, Any],
    *,
    genres: list[str] | None = None,
    genre_key: str | None = None,
    settings: dict[str, Any] | None = None,
    max_tokens: int = 800,
) -> tuple[str, bool, str]:
    path_hash = get_path_hash(seed, path_choices, genre_key=genre_key)

    if path_hash in story_cache:
        cached = story_cache[path_hash]
        if isinstance(cached, dict):
            text = cached.get("segment", "")
        else:
            text = cached
        return text, True, path_hash

    print("Story generating, please wait...")

    chat_history: list[dict[str, str]] = []
    chat_history.extend(BASE_PROMPTS)

    chat_history.append(
        {
            "role": "system",
            "content": (
                f"Player morality: {player_choices['morality']}, "
                f"AstraCore Dynamics: {player_choices['AstraCore Dynamics']}, "
                f"Stellar Concorde Collective: {player_choices['Stellar Concorde Collective']}. "
                f"Major choices: {', '.join(player_choices['major choices'])}."
            ),
        }
    )

    chat_history.extend(build_genre_prompts(genres, genre_key))
    if settings:
        chat_history.extend(build_settings_prompt_constraints(settings))

    if npc_states:
        npc_lines = []
        for npc_id, data in npc_states.items():
            name = data.get("name", npc_id)
            rel = data.get("relationship", 0)
            role = data.get("role") or (
                ", ".join(data.get("roles", [])) if data.get("roles") else "unknown role"
            )
            flags = ", ".join(data.get("flags", [])) if data.get("flags") else "no major history yet"
            npc_lines.append(f"- {name} (id={npc_id}): relationship {rel}, role: {role}, history: {flags}")
        npc_summary = "Current NPCs and your relationship with them:\n" + "\n".join(npc_lines)
        chat_history.append({"role": "system", "content": npc_summary})

        game_state = {
        "inventory": [],
        "flags": {},
        "location": None,
    }

    state_summary = (
        "Current game state:\n"
        f"Inventory: {', '.join(game_state['inventory']) if game_state['inventory'] else 'empty'}\n"
        f"Flags: {', '.join(f'{key}={value}' for key, value in game_state['flags'].items()) if game_state['flags'] else 'none'}\n"
        f"Location: {game_state['location'] if game_state['location'] else 'unknown'}"
    )

    chat_history.append(
        {
            "role": "system",
            "content": state_summary,
        }
    )

    checkpoint_instruction = get_checkpoint_instruction(len(path_choices))
    if checkpoint_instruction:
        chat_history.append(
            {
                "role": "system",
                "content": (
                    "THIS IS AN IMPORTANT THING THAT YOU MUST FOLLOW IN ORDER FOR THE STORY TO MAKE SENSE, "
                    f"FOLLOW IT: {checkpoint_instruction}"
                ),
            }
        )

    if not path_choices:
        chat_history.append(
            {"role": "user", "content": "Begin the story with an opening scene and give 2-3 numbered choices."}
        )
    else:
        context = f"The player previously chose: {' -> '.join(path_choices)}."
        user_message = (
            f"{context}\n\n"
            "Continue the story based on the player's actual action. "
            "The player's action may have been one of the suggested choices "
            "or a completely custom action they came up with themselves. "
            "If the player attempted a custom action, treat that action as "
            "their intended action and respond to it naturally. "
            "The action may succeed, partially succeed, fail, or have "
            "unexpected consequences depending on the situation. "
            "Do not force the story back toward the previously suggested "
            "choices simply because the player chose something different. "
            "Then provide 2-3 new numbered choices."
        )

        chat_history.append({"role": "user", "content": user_message})

    effective_max_tokens = get_max_tokens(settings or {}, fallback=max_tokens)
    effective_temperature = float((settings or {}).get("temperature", 0.7))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_history,
        max_tokens=effective_max_tokens,
        temperature=effective_temperature,
    )

    if response.choices[0].finish_reason == "length":
        print("WARNING: Story generation hit the token limit.")

    text = response.choices[0].message.content.strip()
    story_cache[path_hash] = text
    save_cache()
    print(" " * 40)
    return text, False, path_hash

