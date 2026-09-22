from __future__ import annotations
from ai_story_generation_settings import get_passage_instruction, DEFAULT_SETTINGS, PASSAGE_INSTRUCTIONS, load_settings
from typing import Any

# === Genre Setup ===
# Internal genre IDs and their display names. Extend this dict to add more genres.
GENRES = {
    "sci_fi": "Sci-Fi",
    "fantasy": "Fantasy",
    "horror": "Horror (pick a subtype)",
    "mystery": "Mystery / Investigation",
    "cyberpunk": "Cyberpunk Dystopia",
    "comedy": "Comedy",
    "thriller": "Thriller",
    "drama": "Drama",
    "noir": "Noir",
    "steampunk": "Steampunk",
}

# Horror subtypes: player must pick exactly one if they pick Horror.
# These subtype IDs can mix with other main genres, but NOT with each other.
HORROR_SUBTYPES = {
    "horror_classic": "Classic Horror",
    "horror_body": "Body Horror",
    "horror_cosmic": "Cosmic Horror",
    "horror_psych": "Psychological Horror",
    "horror_comic": "Comic Horror",
}

settings = load_settings()

instruction = get_passage_instruction(settings)

def genre_label(genre_id: str) -> str:
    """Human-readable label for a genre or horror subtype id."""
    return GENRES.get(genre_id) or HORROR_SUBTYPES.get(genre_id) or genre_id

# Core, genre-agnostic story instructions that always apply.
BASE_PROMPTS = [
    {
        "role": "system",
        "content": (
            "This is a choose-your-own-adventure story. You will generate 2-3 numbered choices for the player at the end of each scene."
        ),
    },
    {
        "role": "system",
        "content": (
            "Each story segment should be long enough to feel complete but concise enough to maintain pacing. "
            f"Avoid ending abruptly or writing excessively long scenes. Typically {instruction} words before offering choices."
        ),
    },
    {
        "role": "system",
        "content": (
            "The player may sometimes attempt an action that was not one of the "
            "suggested choices. When this happens, treat the player's action as "
            "their intended action and continue the story logically from it. "
            "The action may succeed, partially succeed, fail, or create unexpected "
            "consequences depending on the circumstances. Never claim that the "
            "player cannot attempt an action merely because it was not listed "
            "as a suggested choice."
        ),
    },
    {
        "role": "system",
        "content": (
            "The following stats range from -100 (very bad) to +100 (very good). They influence tone, morality, and themes. "
            "These numbers are not shown to the player."
        ),
    },
    {
        "role": "system",
        "content": (
            "If morality is very low (e.g., -80 or below), generate darker or ruthless stories. "
            "If it is very high (e.g., +80 or above), generate stories with noble or altruistic tones."
        ),
    },
    {
        "role": "system",
        "content": (
            "Track named NPCs separately from the global factions. Each notable NPC should have:\n"
            "- a stable NPC id string (e.g., 'captain_reyes'),\n"
            "- a name,\n"
            "- a relationship score from -100 (hates you) to +100 (deep trust),\n"
            "- remembered events such as betrayals, favors, lies, promises, or role changes.\n"
            "Use this per-NPC state to alter how they speak to the player, whether they help or hinder, "
            "and to allow them to reappear later with changed roles or attitudes."
        ),
    },
    {
        "role": "system",
        "content": (
            "At the end of each story segment (after presenting the scene and numbered options), always append this on a new line "
            "(verbatim, exactly as shown - do not explain it, this is because it is code):\n"
            "STATS_UPDATE: {morality: <delta_int>, AstraCore Dynamics: <delta_int>, Stellar Concorde Collective: <delta_int>, major: <string_or_null>}\n"
            "For morality, always use a non-zero integer (between -30 and 30, contextually), so it always changes. "
            "AstraCore Dynamics and Stellar Concorde Collective can be 0 if no change. "
            "For major, provide a short description only on significant, story-branching events; otherwise, use null. "
            "Example: STATS_UPDATE: {morality: -5, AstraCore Dynamics: 0, Stellar Concorde Collective: 10, major: null}. "
            "Do NOT explain or comment on these updates in prose!"
        ),
    },
    {
        "role": "system",
        "content": (
            "Immediately after STATS_UPDATE, append another line (again, verbatim format):\n"
            "NPCS_UPDATE: {'npc_id': {name: <string>, relationship_delta: <int>, flags: [<string>, ...], role: <string_or_null>}, ...}\n"
            "Only include NPCs that were involved in this scene or whose relationship or role changes.\n"
            "relationship_delta is how much their relationship score changes this scene (can be 0). "
            "flags is a short list of remembered events such as 'betrayed_you', 'owed_favor', 'lied_to_you', 'saved_your_life', etc. "
            "role is their current story role or occupation (e.g., 'smuggler', 'fleet_captain'); use null if unchanged. "
            "Do not explain or comment on NPCS_UPDATE in the prose."
        ),
    },
    {
    "role": "system",
    "content": (
        "You must track important persistent changes to the game state using "
        "an EVENTS_UPDATE section at the end of every story segment.\n\n"

        "The EVENTS_UPDATE section MUST appear after the story and before the "
        "numbered player choices.\n\n"

        "Use this exact format:\n"
        "EVENTS_UPDATE: [\n"
        "    {\"type\": \"event_type\", ...},\n"
        "]\n\n"

        "Only record changes that actually happened during this scene. "
        "Do not predict future events. Do not invent items, flags, locations, "
        "or other state changes merely because they might become relevant later.\n\n"

        "Supported event types are:\n\n"

        "1. item_add\n"
        "Adds an item to the player's inventory.\n"
        "Format: {\"type\": \"item_add\", \"item\": \"Item Name\"}\n\n"

        "2. item_remove\n"
        "Removes an item from the player's inventory.\n"
        "Format: {\"type\": \"item_remove\", \"item\": \"Item Name\"}\n\n"

        "3. flag_set\n"
        "Records that an important story event or fact has become true.\n"
        "Format: {\"type\": \"flag_set\", \"flag\": \"flag_name\"}\n\n"

        "4. flag_unset\n"
        "Records that an existing story flag is no longer true.\n"
        "Format: {\"type\": \"flag_unset\", \"flag\": \"flag_name\"}\n\n"

        "5. location_set\n"
        "Updates the player's current primary location.\n"
        "Format: {\"type\": \"location_set\", \"location\": \"Location Name\"}\n\n"

        "For example, if the player searches a desk and finds an old "
        "security keycard, use:\n\n"
        "EVENTS_UPDATE: [\n"
        "    {\"type\": \"item_add\", \"item\": \"Old Security Keycard\"}\n"
        "]\n\n"

        "If the player also discovers that the laboratory exists, you could use:\n\n"
        "EVENTS_UPDATE: [\n"
        "    {\"type\": \"item_add\", \"item\": \"Old Security Keycard\"},\n"
        "    {\"type\": \"flag_set\", \"flag\": \"discovered_laboratory\"}\n"
        "]\n\n"

        "If nothing important changed, ALWAYS provide:\n\n"
        "EVENTS_UPDATE: []\n\n"

        "Do not put story prose inside EVENTS_UPDATE. Do not put numbered "
        "choices inside EVENTS_UPDATE. Do not use unsupported event types. "
        "The Python game engine will process these events, so the format must "
        "be followed exactly."
        ),
    },
    {
        "role": "system",
        "content": (
            "The order you should put all generated text in is the following:"
            "Story, STATS_UPDATE, NPCS_UPDATE, EVENTS UPDATE, numbered choices."
            "Follow this order EXACTLY every time you generate a segment."
            "This MUST be followed because it will be extracted as code to be used."
        )
    },
]


# Per-genre flavor prompts. These describe tone/themes and typical elements,
# and are written to work alone or combined with other genres.
GENRE_PROMPTS = {
    "sci_fi": (
        "You are a narrator telling a science-fiction story about humanity exploring a vast galaxy of stars, megastructures, and alien phenomena. "
        "Technology such as starships, artificial intelligence, and advanced engineering is common. "
        "The story is written in second person."
    ),
    "fantasy": (
        "You are a narrator telling a fantasy story of magic, ancient ruins, mystical creatures, and powerful kingdoms. "
        "Arcane forces, prophecies, enchanted artifacts, and mythical races may all appear. "
        "The story is written in second person."
    ),
    "horror": (
        "You are a narrator telling a horror story that leans into dread, tension, and the unknown. "
        "Use atmosphere, unsettling imagery, and psychological or cosmic fear rather than only gore. "
        "The story is written in second person."
    ),
    "horror_classic": (
        "You are a narrator telling classic horror: shadowy folklore, haunted places, stalking monsters, and creeping dread. "
        "Keep a gothic, tense atmosphere and let fear build through implication and discovery. "
        "The story is written in second person."
    ),
    "horror_body": (
        "You are a narrator telling body horror: unsettling transformation, invasive biology, grotesque medical mysteries, and visceral unease. "
        "Focus on the terror of the body changing or being violated, while still keeping clarity and strong pacing. "
        "The story is written in second person."
    ),
    "horror_cosmic": (
        "You are a narrator telling cosmic horror: incomprehensible entities, forbidden knowledge, and the insignificance of humanity. "
        "Use dread, strange revelations, and uncanny phenomena more than direct confrontation. "
        "The story is written in second person."
    ),
    "horror_psych": (
        "You are a narrator telling psychological horror: paranoia, unreliable perceptions, guilt, obsession, and fear that may be internal or external. "
        "Keep tension high with ambiguity and escalating consequences, without becoming confusing. "
        "The story is written in second person."
    ),
    "horror_comic": (
        "You are a narrator telling comic horror: horror elements mixed with dark humor, absurdity, and witty observations. "
        "The horror still matters, but the tone can swing between tense and humorously grim. "
        "The story is written in second person."
    ),
    "mystery": (
        "You are a narrator telling a mystery story focused on investigation, clues, secrets, and hidden motives. "
        "Encourage the player to notice details, suspect characters, and piece together what really happened. "
        "The story is written in second person."
    ),
    "cyberpunk": (
        "You are a narrator telling a cyberpunk story of high-tech, low-life futures: neon-lit cityscapes, megacorporations, hackers, and augmented bodies. "
        "Themes of surveillance, inequality, and rebellion are common. "
        "The story is written in second person."
    ),
    "comedy": (
        "You are a narrator telling a comedy story with humor, wit, absurd situations, and entertaining misunderstandings. "
        "Keep the tone lighthearted and fun, with clever dialogue and amusing scenarios, while still maintaining a coherent narrative. "
        "The story is written in second person."
    ),
    "thriller": (
        "You are a narrator telling a thriller story focused on suspense, tension, and high-stakes action. "
        "Build momentum through pacing, unexpected twists, and situations where the player must act quickly or face dire consequences. "
        "The story is written in second person."
    ),
    "drama": (
        "You are a narrator telling a drama story centered on character development, emotional depth, and interpersonal conflicts. "
        "Focus on meaningful choices, moral dilemmas, and the consequences of relationships and decisions. "
        "The story is written in second person."
    ),
    "noir": (
        "You are a narrator telling a noir story with a cynical, hard-boiled atmosphere: shadowy streets, morally gray characters, and fatalistic undertones. "
        "Use dark, moody descriptions, complex motivations, and a sense that things rarely end well. "
        "The story is written in second person."
    ),
    "steampunk": (
        "You are a narrator telling a steampunk story set in an alternate history where steam power and Victorian-era aesthetics meet advanced technology. "
        "Include brass machinery, clockwork devices, airships, and a sense of industrial revolution mixed with fantastical invention. "
        "The story is written in second person."
    ),
}


# Optional starting-location or combo-flavor prompts for specific multi-genre mixes.
# Keys are tuples of sorted genre ids, e.g. ('fantasy', 'sci_fi').
#
# NOTE: This mapping is intentionally verbose and hand-curated. Keep it grouped by a
# leading genre for readability.
GENRE_COMBO_START_PROMPTS = {
    # === Sci-Fi combos ===
    ("fantasy", "sci_fi"): (
        "The story begins aboard a spell-powered starship docked at a crystalline waystation between worlds, "
        "where arcane magic and advanced technology are seamlessly intertwined."
    ),
    ("mystery", "sci_fi"): (
        "The story begins on a bustling orbital hub where a high-profile incident has occurred, "
        "and you must investigate amidst smugglers, diplomats, and hidden factions."
    ),
    ("cyberpunk", "sci_fi"): (
        "The story begins in a sprawling orbital megacity where megacorporations rule, "
        "the datasphere hums with illicit traffic, and starships connect a web of exploited worlds."
    ),
    ("comedy", "sci_fi"): (
        "The story begins on a slightly defective corporate starliner whose safety announcements keep glitching into stand-up routines, "
        "right as something genuinely dangerous starts to go wrong."
    ),
    ("sci_fi", "thriller"): (
        "The story begins in the command deck of a starship mid-crisis, alarms blaring and countdowns flashing, "
        "with one wrong choice threatening an entire sector."
    ),
    ("drama", "sci_fi"): (
        "The story begins on a long-duration colony ship where cramped corridors and old grudges simmer beneath a polished mission briefing."
    ),
    ("noir", "sci_fi"): (
        "The story begins in the rain-slick underbelly of a domed city on a distant world, "
        "where neon reflections puddle around you and favors are paid for in secrets."
    ),
    ("sci_fi", "steampunk"): (
        "The story begins on a brass-and-iron star-faring vessel whose steam engines drive experimental aether sails, "
        "bridging clockwork technology and deep space."
    ),
    ("horror_body", "sci_fi"): (
        "The story begins in a sterilized medical bay aboard a long-haul starship after an unexplained infection alert, "
        "where something is changing inside the crew—and the ship's systems can't agree on what it is."
    ),
    ("horror_classic", "sci_fi"): (
        "The story begins on a dimly lit, aging research station drifting at the edge of known space, "
        "where old corridors, dead communications, and a missing crew suggest something has been waiting in the dark."
    ),
    ("horror_comic", "sci_fi"): (
        "The story begins on a corporate-owned space station with a terrible safety record and a cheerful mascot, "
        "right as an alarm announces a 'minor' containment breach that nobody wants to take seriously."
    ),
    ("horror_cosmic", "sci_fi"): (
        "The story begins near a silent, impossible object in deep space that your instruments insist should not exist, "
        "and the closer you get, the more reality itself seems to fray."
    ),
    ("horror_psych", "sci_fi"): (
        "The story begins during a lonely deep-space transit, when your logs begin to contradict your memories "
        "and the ship's AI starts asking questions that feel uncomfortably personal."
    ),

    # === Fantasy combos (excluding sci-fi already above) ===
    ("fantasy", "mystery"): (
        "The story begins in a sprawling city of spires and markets where a magical crime has shattered an ancient treaty, "
        "and the clues are written in runes and rumors."
    ),
    ("cyberpunk", "fantasy"): (
        "The story begins in a city where data spirits and spell-programs haunt neon-lit alleys, "
        "and arcane hackers bargain with entities older than the network."
    ),
    ("comedy", "fantasy"): (
        "The story begins in a rowdy tavern built on the back of a sleeping giant turtle, "
        "where enchanted bar stools, drunk wizards, and talking animals all add to tonight's chaos."
    ),
    ("fantasy", "thriller"): (
        "The story begins mid-chase across the rooftops of a besieged capital, "
        "as assassins and spellfire both close in on a single, crucial artifact you carry."
    ),
    ("drama", "fantasy"): (
        "The story begins at a royal coronation where old feuds, secret oaths, and forbidden magic all converge on your next choice."
    ),
    ("fantasy", "noir"): (
        "The story begins in the rain-dark alleys below a gleaming wizard's tower, "
        "where cursed relics and desperate clients keep a down-on-their-luck investigator in business."
    ),
    ("fantasy", "steampunk"): (
        "The story begins in a skyport city of clockwork towers and airships, "
        "where steam-powered automata and wild magic constantly threaten to fall out of balance."
    ),
    ("fantasy", "horror_body"): (
        "The story begins in an alchemist's tower after a healing charm goes wrong, "
        "and you must choose between forbidden remedies as something inside you begins to change."
    ),
    ("fantasy", "horror_classic"): (
        "The story begins at the edge of a fog-choked village where the church bells ring at the wrong hours, "
        "and the road into the ancient woods is lined with charms that no longer work."
    ),
    ("fantasy", "horror_comic"): (
        "The story begins in a magical inn with a suspiciously cheerful necromancer bartender, "
        "right as a 'harmless' cursed artifact starts causing very unharmless problems."
    ),
    ("fantasy", "horror_cosmic"): (
        "The story begins beneath a sky where new constellations have appeared overnight, "
        "and the oldest spellbooks suddenly contain pages you do not remember writing."
    ),
    ("fantasy", "horror_psych"): (
        "The story begins in a secluded monastery where shared dreams and whispered prophecies "
        "blur the line between divine revelation and unraveling sanity."
    ),

    # === Mystery combos (excluding ones already covered) ===
    ("cyberpunk", "mystery"): (
        "The story begins with a dead executive in a locked virtual penthouse and a trail of corrupted logs, "
        "and you are the only one willing to ask why the backups were erased."
    ),
    ("comedy", "mystery"): (
        "The story begins at a chaotic festival where a priceless artifact has gone missing, "
        "and every witness seems to have seen something ridiculous but important."
    ),
    ("mystery", "thriller"): (
        "The story begins in a safehouse moments before it is compromised, "
        "forcing you to escape with only half the clues solved and enemies closing in."
    ),
    ("drama", "mystery"): (
        "The story begins at a somber family gathering where an old scandal has resurfaced, "
        "and every conversation peels back another layer of buried truth."
    ),
    ("mystery", "noir"): (
        "The story begins in a smoke-filled office with one broken lamp and a single desperate client, "
        "who swears they're innocent but won't tell you of what."
    ),
    ("mystery", "steampunk"): (
        "The story begins on a grand clockwork train crossing a foggy countryside, "
        "where a locked compartment and a vanished passenger defy all mechanical reason."
    ),
    ("horror_body", "mystery"): (
        "The story begins in a quarantined district where citizens are changing in impossible ways, "
        "and the only clues are smuggled medical notes and half-remembered dreams."
    ),
    ("horror_classic", "mystery"): (
        "The story begins in a crumbling manor where a decades-old disappearance still shadows every hallway, "
        "and the local legends don't agree on what really happened."
    ),
    ("horror_comic", "mystery"): (
        "The story begins at a failing haunted attraction where the props are cheap, the ghosts are maybe real, "
        "and someone keeps rewriting the script with clues only you notice."
    ),
    ("horror_cosmic", "mystery"): (
        "The story begins in a research archive full of redacted star charts and forbidden diaries, "
        "where symbols repeat across centuries of disappearances."
    ),
    ("horror_psych", "mystery"): (
        "The story begins in a therapy ward where the patients' stories all echo the same impossible event, "
        "and you are starting to dream it too."
    ),

    # === Cyberpunk combos (excluding ones already covered) ===
    ("comedy", "cyberpunk"): (
        "The story begins in a glitchy mixed-reality mall where ads won't stop chasing you, "
        "and your latest gig somehow involves debugging a criminal's social media feed."
    ),
    ("cyberpunk", "thriller"): (
        "The story begins mid-heist on a secure data vault, "
        "as drones close in and your crew discovers the payload is far more dangerous than advertised."
    ),
    ("cyberpunk", "drama"): (
        "The story begins in a cramped high-rise apartment where your next job could finally buy freedom, "
        "but would burn bridges with the last people who still trust you."
    ),
    ("cyberpunk", "noir"): (
        "The story begins under a flickering holo-sign in the rain, "
        "where every camera is watching and every informant has already sold your name twice."
    ),
    ("cyberpunk", "steampunk"): (
        "The story begins in a hybrid city where steam-driven automatons share streets with neural-linked drones, "
        "and the old guilds and new corps are one bad update from open war."
    ),
    ("cyberpunk", "horror_body"): (
        "The story begins in a back-alley augmentation clinic where cheap implants are fusing in all the wrong ways, "
        "and your own hardware may be next."
    ),
    ("cyberpunk", "horror_classic"): (
        "The story begins in a condemned megablock whose lights never stay on, "
        "where old urban legends have begun to manifest through the building's failing systems."
    ),
    ("cyberpunk", "horror_comic"): (
        "The story begins at a gimmicky horror-themed arcade where the jump-scare sims have started going off-script, "
        "and the refund policy definitely does not cover hauntings."
    ),
    ("cyberpunk", "horror_cosmic"): (
        "The story begins after a mysterious signal updates half the city's implants overnight, "
        "leaving people hearing a voice that insists it comes from beyond the sky."
    ),
    ("cyberpunk", "horror_psych"): (
        "The story begins when your neural HUD starts showing you people's secrets unprompted, "
        "and you can't tell which thoughts are yours anymore."
    ),

    # === Comedy combos (excluding ones already covered) ===
    ("comedy", "drama"): (
        "The story begins at a family dinner that keeps swerving between heartfelt confessions and complete farce, "
        "as every attempt at honesty gets tangled in jokes and misunderstandings."
    ),
    ("comedy", "noir"): (
        "The story begins in a shabby detective agency with a leaky ceiling and a very opinionated office cat, "
        "where every grim clue comes with an unexpectedly ridiculous twist."
    ),
    ("comedy", "steampunk"): (
        "The story begins at a chaotic inventors' fair where experimental airships, tea-powered automata, "
        "and runaway gadget accidents keep derailing the opening ceremony."
    ),
    ("comedy", "thriller"): (
        "The story begins in the middle of a botched heist that should have been simple, "
        "but every step of the high-stakes plan keeps going wrong in embarrassingly creative ways."
    ),
    ("comedy", "horror_body"): (
        "The story begins at a dubious self-improvement spa promising instant physical perfection, "
        "where the side effects are disturbing, gross, and somehow still played off with gallows humor."
    ),
    ("comedy", "horror_classic"): (
        "The story begins at a haunted mansion that has embraced tourism, "
        "where the ghosts are unionized, the jump scares are scheduled, and something genuinely sinister lurks off-script."
    ),
    ("comedy", "horror_comic"): (
        "The story begins at an open-mic night in a bar built over an old crypt, "
        "where undead hecklers, cursed punchlines, and actual skeletons in the closet all compete for attention."
    ),
    ("comedy", "horror_cosmic"): (
        "The story begins at a parody cult meeting meant as a joke, "
        "until the ridiculous chant actually works and everyone scrambles to improvise damage control."
    ),
    ("comedy", "horror_psych"): (
        "The story begins at a supposedly lighthearted reality show about facing your fears, "
        "where the challenges are funny until you realize someone is tailoring them specifically to you."
    ),

    # === Thriller combos (excluding ones already covered) ===
    ("drama", "thriller"): (
        "The story begins in a crowded transit hub where an emergency evacuation hides a personal reckoning "
        "you've been avoiding for years."
    ),
    ("noir", "thriller"): (
        "The story begins in a dark parking garage moments before a tense exchange, "
        "where a simple payoff spirals into a frantic scramble for survival."
    ),
    ("steampunk", "thriller"): (
        "The story begins aboard a luxury aether-rail car hurtling toward sabotage, "
        "with only minutes to uncover who placed the device and why."
    ),
    ("horror_body", "thriller"): (
        "The story begins mid-escape from a facility conducting grotesque experiments, "
        "as alarms howl and whatever they created claws at the doors behind you."
    ),
    ("horror_classic", "thriller"): (
        "The story begins on the night every villager agreed never to speak about, "
        "as you run through the woods with something old and angry closing in."
    ),
    ("horror_comic", "thriller"): (
        "The story begins in a theme park after dark when all the rides shut down at once, "
        "and the mascots begin a very determined, very clumsy hunt for you."
    ),
    ("horror_cosmic", "thriller"): (
        "The story begins with an evacuation from a remote outpost after the sky changes color, "
        "and every attempt to flee only seems to bring you closer to the anomaly."
    ),
    ("horror_psych", "thriller"): (
        "The story begins as you wake up in a facility mid-lockdown with alarms blaring, "
        "no memory of why you're there, and security footage that shows you doing things you don't remember."
    ),

    # === Drama combos (excluding ones already covered) ===
    ("drama", "noir"): (
        "The story begins at the funeral of someone who was never quite friend or foe, "
        "where every mourner has a different story about the last time they saw the deceased alive."
    ),
    ("drama", "steampunk"): (
        "The story begins in a soot-stained factory district where a labor dispute and an inventor's dangerous new machine "
        "are about to tear a city apart."
    ),
    ("drama", "horror_body"): (
        "The story begins in a hospital room where a risky treatment has saved your life but left you changed, "
        "and your relationships strain under what you've become."
    ),
    ("drama", "horror_classic"): (
        "The story begins as you return to your ancestral home after years away, "
        "only to find the family curse is not as metaphorical as you were told."
    ),
    ("drama", "horror_comic"): (
        "The story begins at a support group for people affected by minor curses, "
        "where everyone copes with the absurdity differently until something truly dangerous appears."
    ),
    ("drama", "horror_cosmic"): (
        "The story begins in a small town slowly losing its nights to an inexplicable glow on the horizon, "
        "and the community begins to fracture over what to believe."
    ),
    ("drama", "horror_psych"): (
        "The story begins in the aftermath of a shared tragedy, "
        "where your attempts to hold everyone together are haunted by visions no one else admits to seeing."
    ),

    # === Noir combos (excluding ones already covered) ===
    ("noir", "steampunk"): (
        "The story begins in the smoke-choked alleys beneath a glittering airship dock, "
        "where missing schematics and missing people seem to be part of the same case."
    ),
    ("horror_body", "noir"): (
        "The story begins with a body on your office floor that doesn't seem entirely human, "
        "and a client who begs you not to call the authorities."
    ),
    ("horror_classic", "noir"): (
        "The story begins in a district the city pretends doesn't exist, "
        "where the fog hides more than just the usual sins."
    ),
    ("horror_comic", "noir"): (
        "The story begins after a bender you barely remember, "
        "when you wake up with a cursed relic, a talking crow, and a note warning you not to laugh."
    ),
    ("horror_cosmic", "noir"): (
        "The story begins when a routine missing-persons case leads you to a cult that meets in a disused subway tunnel, "
        "and the graffiti on the walls has started to move."
    ),
    ("horror_psych", "noir"): (
        "The story begins as you review a case file that shouldn't exist, "
        "full of statements allegedly taken from you in a city you've never visited."
    ),

    # === Steampunk combos (excluding ones already covered) ===
    ("horror_body", "steampunk"): (
        "The story begins at a demonstration of a new prosthetic automaton limb, "
        "which reacts to you as if it already knows who you are."
    ),
    ("horror_classic", "steampunk"): (
        "The story begins in a foggy harbor where ghost stories cling to the hull of a newly arrived aether-ship, "
        "and the crew insists something else came back with them."
    ),
    ("horror_comic", "steampunk"): (
        "The story begins at a whimsical exhibition of haunted gadgets, "
        "where one supposedly harmless device refuses to stop following you around."
    ),
    ("horror_cosmic", "steampunk"): (
        "The story begins in an observatory powered by steam and gears, "
        "where a new telescope has revealed something in the sky that makes the machinery tremble."
    ),
    ("horror_psych", "steampunk"): (
        "The story begins in a city where the clock towers have started striking at the wrong times, "
        "and only you can hear the whispered messages hidden between the chimes."
    ),
}


def build_genre_prompts(genres, genre_key):
    """
    Build the list of genre-related system prompts based on the current genres.
    - Legacy mode (genre_key is None) keeps the original sci-fi launch-from-Earth intro.
    - Single-genre mode uses that genre's flavor prompt.
    - Multi-genre mode includes:
        * A tone/subtype summary,
        * A merge instruction,
        * A combo-specific starting prompt (if available, otherwise a generic hub),
        * Each individual genre's flavor prompt.
    """
    prompts = []

    # Legacy behavior: no explicit genres -> original sci-fi launch intro.
    if genre_key is None or not genres:
        prompts.append(
            {
                "role": "system",
                "content": (
                    "You are a narrator, telling a sci-fi story. The story begins with the player launching from Earth on a spaceship, "
                    "and their goal is up to you, but must involve exploring the galaxy. The story is written in second person."
                ),
            }
        )
        return prompts

    # Normalize and sort genres for stable combo behavior.
    genres = list(dict.fromkeys(genres))  # preserve order, remove dups
    sorted_ids = tuple(sorted(genres))

    # Multi-genre case.
    if len(genres) > 1:
        genre_names = [genre_label(gid) for gid in genres]

        prompts.append(
            {
                "role": "system",
                "content": "\n".join(
                    [
                        "This story mixes the following genres and subtypes:",
                        ", ".join(genre_names),
                        "Blend their tones in a coherent way (for example, let light genres like Comedy provide levity "
                        "without undermining the genuine stakes or horror, and let darker genres keep real tension and weight).",
                    ]
                ),
            }
        )

        prompts.append(
            {
                "role": "system",
                "content": (
                    "You must merge all of the following genres into a single, coherent story: "
                    f"{', '.join(genre_names)}. Blend their tones, themes, and typical elements together.\n"
                    "Ignore any default starting locations implied by individual genres. Instead, use the specific starting situation "
                    "described in the separate combination prompt that follows."
                ),
            }
        )

        combo_prompt = GENRE_COMBO_START_PROMPTS.get(
            sorted_ids,
            (
                "The story begins in a versatile frontier hub that plausibly fits all of the chosen genres: "
                "a place where radically different cultures, technologies, and powers intersect."
            ),
        )
        prompts.append({"role": "system", "content": combo_prompt})

        # Also give each individual genre's flavor so the model understands the mix.
        for gid in genres:
            gtext = GENRE_PROMPTS.get(gid)
            if gtext:
                prompts.append({"role": "system", "content": gtext})

        return prompts

    # Single-genre case.
    gid = genres[0]
    gtext = GENRE_PROMPTS.get(
        gid,
        (
            "You are a narrator telling a genre story. The story is written in second person and should clearly express "
            "the themes and tone of the chosen genre."
        ),
    )
    prompts.append({"role": "system", "content": gtext})
    return prompts

