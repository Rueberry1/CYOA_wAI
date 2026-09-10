from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ai_story_generation_core import (
    CHECKPOINTS,
    extract_choices,
    extract_npcs_update,
    extract_stats_update,
    generate_story_segment,
    clamp,
    story_cache,
    save_cache,
    clear_cache,
)
from ai_story_generation_genres import GENRES, HORROR_SUBTYPES, genre_label
from ai_story_generation_settings import load_settings, save_settings


def choose_your_own_adventure(
    console: Console,
    seed: int,
    player_choices: dict[str, Any],
    *,
    genres=None,
    genre_key=None,
    settings: dict[str, Any] | None = None,
):
    holostar = "[bold cyan]*[/]"
    if genres:
        pretty_genres = " + ".join(genre_label(g) for g in genres)
        subtitle_text = f"{holostar*3} {pretty_genres} {holostar*3}"
    else:
        subtitle_text = f"{holostar*3} Legacy Sci-Fi (no explicit genre) {holostar*3}"

    header = Panel(
        Text("HOLOTERMINAL\nChoose Your Own Adventure", style="bold cyan"),
        style="bold bright_blue",
        subtitle=subtitle_text,
    )
    footer = Panel(Text("Type the number of your choice and press <Enter>", style="cyan"), style="bright_blue")

    console.clear()
    console.print(header)
    path_choices: list[str] = []
    npc_states: dict[str, Any] = {}

    while True:
        segment, used_cache, path_hash = generate_story_segment(
            seed,
            player_choices,
            path_choices,
            npc_states,
            genres=genres,
            genre_key=genre_key,
            settings=settings,
        )

        cached_entry = story_cache.get(path_hash)
        if used_cache and isinstance(cached_entry, dict):
            cached_npcs = cached_entry.get("npcs")
            if isinstance(cached_npcs, dict):
                npc_states.clear()
                npc_states.update(cached_npcs)

        story_part = segment.split("STATS_UPDATE")[0].strip()
        story_panel = Panel(
            Text(story_part, style="bright_cyan"),
            style="bold bright_blue",
            border_style="bold bright_cyan",
            width=80,
            title=f"Scene {len(path_choices)+1}",
        )
        console.print(story_panel)

        if len(path_choices) >= max(CHECKPOINTS.keys()):
            console.print(Panel("[bold green]The story concludes here. You have reached the final checkpoint![/]", style="cyan"))
            break

        options = extract_choices(segment)
        if not options:
            console.print(Panel("[bold magenta]The story ends here. No more choices.[/]", style="magenta"))
            break

        table = Table(box=None, show_header=False, expand=False, border_style="bright_blue")
        for idx, option in enumerate(options):
            table.add_row(f"[bold blue]{idx+1}.[/] [bright_white]{option}")
        console.print(table)
        console.print(footer)

        while True:
            try:
                choice = Prompt.ask("[bold cyan]Select your choice[/]", choices=[str(i+1) for i in range(len(options))])
                choice_int = int(choice)
                if 1 <= choice_int <= len(options):
                    break
            except ValueError:
                pass
            console.print("[bright_red]Invalid choice. Try again.[/]")

        chosen_text = options[choice_int - 1]
        path_choices.append(chosen_text)

        stats_update = extract_stats_update(segment)
        if stats_update:
            player_choices["morality"] = clamp(player_choices["morality"] + stats_update["morality"], -100, 100)
            player_choices["AstraCore Dynamics"] = clamp(player_choices["AstraCore Dynamics"] + stats_update["AstraCore Dynamics"], -100, 100)
            player_choices["Stellar Concorde Collective"] = clamp(player_choices["Stellar Concorde Collective"] + stats_update["Stellar Concorde Collective"], -100, 100)
            major = stats_update.get("major", None)
            if major and str(major).lower() not in ("null", "none", ""):
                player_choices["major choices"].append(str(major))

        npcs_update = extract_npcs_update(segment)
        if npcs_update:
            for npc_id, npc_data in npcs_update.items():
                if not isinstance(npc_data, dict):
                    continue
                name = str(npc_data.get("name", npc_id))
                try:
                    rel_delta = int(npc_data.get("relationship_delta", 0))
                except Exception:
                    rel_delta = 0
                flags = npc_data.get("flags", [])
                if not isinstance(flags, (list, tuple)):
                    flags = [str(flags)]
                role = npc_data.get("role", None)

                existing = npc_states.get(
                    npc_id,
                    {
                        "name": name,
                        "relationship": 0,
                        "flags": [],
                        "roles": [],
                    },
                )

                existing["name"] = name
                existing["relationship"] = clamp(existing.get("relationship", 0) + rel_delta, -100, 100)

                flag_set = set(str(f) for f in existing.get("flags", []))
                for f in flags:
                    if f is None:
                        continue
                    flag_set.add(str(f))
                existing["flags"] = sorted(flag_set)

                if role and str(role).lower() not in ("null", "none", ""):
                    role_str = str(role)
                    roles_list = list(existing.get("roles", []))
                    roles_list.append(role_str)
                    existing["roles"] = roles_list
                    existing["role"] = role_str

                npc_states[npc_id] = existing

        story_cache[path_hash] = {"segment": segment, "npcs": npc_states}
        save_cache()


def start_new_game(console: Console, player_choices: dict[str, Any], settings: dict[str, Any]) -> None:
    try:
        input_seed = Prompt.ask("[bold cyan]Enter a seed number (or press Enter for default 12345)[/]")
        seed = 12345 if input_seed.strip() == "" else int(input_seed)
    except Exception:
        seed = 12345
        console.print("[bright_red]Invalid seed entered. Using default: 12345[/]")

    console.print()
    console.print(Panel(Text("Select one or more genres (comma-separated).", style="bold cyan"), style="bright_blue"))
    console.print("[bold cyan]Available genres:[/]")
    index_to_id = {}
    for idx, (gid, label) in enumerate(GENRES.items(), start=1):
        console.print(f"[bold blue]{idx}[/]: [bright_white]{label}[/] [dim]({gid})[/]")
        index_to_id[str(idx)] = gid
    console.print("[bold blue]0[/]: [bright_white]Legacy default (original sci-fi launch from Earth)[/]")

    try:
        raw_genres = Prompt.ask(
            "[bold cyan]Enter genre numbers (e.g., 1 or 1,3) or leave blank and press Enter for legacy default[/]",
            default="",
        )
    except EOFError:
        raw_genres = ""

    genres = None
    genre_key = None
    raw_genres = (raw_genres or "").strip()
    if raw_genres:
        parts = [p.strip() for p in raw_genres.split(",") if p.strip() != ""]
        selected_ids: list[str] = []
        use_legacy = False
        for p in parts:
            if p == "0":
                use_legacy = True
                break
            gid = index_to_id.get(p)
            if gid and gid not in selected_ids:
                selected_ids.append(gid)

        if not use_legacy and selected_ids:
            if "horror" in selected_ids:
                selected_ids = [gid for gid in selected_ids if gid != "horror"]
                console.print()
                console.print(Panel(Text("Horror selected — choose exactly ONE horror subtype.", style="bold magenta"), style="magenta"))
                subtype_index_to_id = {}
                for sidx, (sid, slabel) in enumerate(HORROR_SUBTYPES.items(), start=1):
                    console.print(f"[bold magenta]{sidx}[/]: [bright_white]{slabel}[/] [dim]({sid})[/]")
                    subtype_index_to_id[str(sidx)] = sid

                try:
                    raw_sub = Prompt.ask(
                        "[bold magenta]Select horror subtype number[/]",
                        choices=list(subtype_index_to_id.keys()),
                    )
                except EOFError:
                    raw_sub = "1"

                subtype_id = subtype_index_to_id.get(str(raw_sub))
                if subtype_id:
                    selected_ids.append(subtype_id)

            genres = selected_ids
            genre_key = "+".join(sorted(selected_ids))

    choose_your_own_adventure(console, seed, player_choices, genres=genres, genre_key=genre_key, settings=settings)


def _settings_summary_table(settings: dict[str, Any]) -> Table:
    table = Table(box=None, show_header=False, expand=False, border_style="bright_blue")
    table.add_row("[bold blue]1.[/] [bright_white]Passage length[/]", f"[cyan]{settings.get('passage_length')}[/]")
    table.add_row("[bold blue]2.[/] [bright_white]Content & style toggles[/]", "[cyan]Configure[/]")
    table.add_row("[bold blue]3.[/] [bright_white]Clear save data[/]", "[cyan]story_cache.json[/]")
    table.add_row("[bold blue]4.[/] [bright_white]Back to main menu[/]", "")
    return table


def _toggle_bool(settings: dict[str, Any], key: str) -> None:
    settings[key] = not bool(settings.get(key, False))
    save_settings(settings)


def _content_style_menu(console: Console, settings: dict[str, Any]) -> None:
    while True:
        console.clear()
        header = Panel(Text("HOLOTERMINAL\nContent & Style Toggles", style="bold cyan"), style="bold bright_blue")
        console.print(header)
        table = Table(box=None, show_header=False, expand=False, border_style="bright_blue")
        table.add_row("[bold blue]1.[/] [bright_white]Allow fourth-wall breaks[/]", f"[cyan]{settings.get('allow_fourth_wall')}[/]")
        table.add_row("[bold blue]2.[/] [bright_white]Single location only[/]", f"[cyan]{settings.get('single_location_only')}[/]")
        table.add_row("[bold blue]3.[/] [bright_white]Allow steamy scenes[/]", f"[cyan]{settings.get('allow_steamy_scenes')}[/]")
        table.add_row("[bold blue]4.[/] [bright_white]Profanity level[/]", f"[cyan]{settings.get('profanity_level')}[/]")
        table.add_row("[bold blue]5.[/] [bright_white]Violence/gore level[/]", f"[cyan]{settings.get('violence_gore_level')}[/]")
        table.add_row("[bold blue]6.[/] [bright_white]Romance focus[/]", f"[cyan]{settings.get('romance_focus')}[/]")
        table.add_row("[bold blue]7.[/] [bright_white]Back[/]", "")
        console.print(table)

        choice = Prompt.ask("[bold cyan]Select an option[/]", choices=["1", "2", "3", "4", "5", "6", "7"])
        if choice == "1":
            _toggle_bool(settings, "allow_fourth_wall")
        elif choice == "2":
            _toggle_bool(settings, "single_location_only")
        elif choice == "3":
            _toggle_bool(settings, "allow_steamy_scenes")
        elif choice == "4":
            level = Prompt.ask("[bold cyan]Profanity level[/]", choices=["none", "mild", "allow"])
            settings["profanity_level"] = level
            save_settings(settings)
        elif choice == "5":
            level = Prompt.ask("[bold cyan]Violence/gore level[/]", choices=["low", "medium", "high"])
            settings["violence_gore_level"] = level
            save_settings(settings)
        elif choice == "6":
            level = Prompt.ask("[bold cyan]Romance focus[/]", choices=["off", "low", "medium", "high"])
            settings["romance_focus"] = level
            save_settings(settings)
        elif choice == "7":
            return


def _passage_length_menu(console: Console, settings: dict[str, Any]) -> None:
    presets = {
        "1": "200_words",
        "2": "400_words",
        "3": "600_words",
        "4": "800_words",
        "5": "1000_words",
        "6": "no_limit",
    }
    console.clear()
    header = Panel(Text("HOLOTERMINAL\nPassage Length", style="bold cyan"), style="bold bright_blue")
    console.print(header)
    table = Table(box=None, show_header=False, expand=False, border_style="bright_blue")
    table.add_row("[bold blue]1.[/] [bright_white]~200 words[/]")
    table.add_row("[bold blue]2.[/] [bright_white]~400 words[/]")
    table.add_row("[bold blue]3.[/] [bright_white]~600 words[/]")
    table.add_row("[bold blue]4.[/] [bright_white]~800 words[/]")
    table.add_row("[bold blue]5.[/] [bright_white]~1000 words[/]")
    table.add_row("[bold blue]6.[/] [bright_white]No limit[/]")
    console.print(table)

    choice = Prompt.ask("[bold cyan]Select passage length[/]", choices=["1", "2", "3", "4", "5", "6"])
    settings["passage_length"] = presets[choice]
    save_settings(settings)
    console.print(Panel(Text(f"Passage length set to: {settings['passage_length']}", style="green"), style="bright_blue"))
    _ = Prompt.ask("[bold cyan]Press Enter to return to Settings[/]", default="")


def settings_menu(console: Console, settings: dict[str, Any]) -> None:
    while True:
        console.clear()
        header = Panel(Text("HOLOTERMINAL\nSettings", style="bold cyan"), style="bold bright_blue")
        console.print(header)
        console.print(_settings_summary_table(settings))

        try:
            choice = Prompt.ask("[bold cyan]Select an option[/]", choices=["1", "2", "3", "4"])
        except EOFError:
            return

        if choice == "1":
            _passage_length_menu(console, settings)
        elif choice == "2":
            _content_style_menu(console, settings)
        elif choice == "3":
            confirm = Prompt.ask(
                "[bold red]This will erase all cached story progress. Are you sure?[/]",
                choices=["1", "2"],
                default="2",
            )
            if confirm == "1":
                clear_cache()
                console.print(Panel(Text("Save data cleared.", style="green"), style="bright_blue"))
                _ = Prompt.ask("[bold cyan]Press Enter to continue[/]", default="")
        elif choice == "4":
            return


def main_menu(console: Console, player_choices: dict[str, Any]) -> None:
    settings = load_settings()
    while True:
        console.clear()
        holostar = "[bold cyan]*[/]"
        header = Panel(
            Text("HOLOTERMINAL\nMain Menu", style="bold cyan"),
            style="bold bright_blue",
            subtitle=f"{holostar*3} Story Engine {holostar*3}",
        )
        console.print(header)

        table = Table(box=None, show_header=False, expand=False, border_style="bright_blue")
        table.add_row("[bold blue]1.[/] [bright_white]Play[/]")
        table.add_row("[bold blue]2.[/] [bright_white]Settings[/]")
        table.add_row("[bold blue]3.[/] [bright_white]Quit[/]")
        console.print(table)

        try:
            choice = Prompt.ask("[bold cyan]Select an option[/]", choices=["1", "2", "3"])
        except EOFError:
            return

        if choice == "1":
            start_new_game(console, player_choices, settings)
        elif choice == "2":
            settings_menu(console, settings)
        elif choice == "3":
            return

