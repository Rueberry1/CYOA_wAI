import sys
import subprocess


# --- INSTALL DEPENDENCIES ---
def install(package: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    from rich.console import Console
except ImportError:
    install("rich")
    from rich.console import Console

try:
    import openai  # noqa: F401
except ImportError:
    install("openai")


from ai_story_generation_ui import main_menu  # noqa: E402


def run() -> None:
    console = Console()
    player_choices = {
        "morality": 20,
        "AstraCore Dynamics": 0,
        "Stellar Concorde Collective": 0,
        "major choices": ["began their story"],
    }
    main_menu(console, player_choices)


if __name__ == "__main__":
    run()
