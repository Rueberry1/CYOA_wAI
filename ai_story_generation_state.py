from __future__ import annotations

from typing import Any


def create_game_state(player_choices: dict[str, Any]) -> dict[str, Any]:
    return {
        "player": player_choices,
        "inventory": [],
        "npcs": {},
        "flags": {},
        "location": None,
    }

def apply_event(game_state: dict[str, Any], event: dict[str, Any]) -> None:
    event_type = event.get("type")

    if event_type == "item_add":
        item = event.get("item")

        if item and item not in game_state["inventory"]:
            game_state["inventory"].append(item)

    elif event_type == "item_remove":
        item = event.get("item")

        if item in game_state["inventory"]:
            game_state["inventory"].remove(item)

    elif event_type == "flag_set":
        flag = event.get("flag")

        if flag:
            game_state["flags"][flag] = True

    elif event_type == "flag_unset":
        flag = event.get("flag")

        if flag:
            game_state["flags"][flag] = False

    elif event_type == "location_set":
        location = event.get("location")

        if location:
            game_state["location"] = location
    else:
        print(f"WARNING: Unknown event type: {event_type}") # debugging tool, to be removed for final release
