# CYOA_wAI 🚀

**An AI-powered choose-your-own-adventure game that creates a unique story around your choices.**

Play entirely in the terminal, choose from a wide variety of genres and settings, and let AI generate the story as you play.

---

## ✨ Features

* 🤖 **AI-generated stories**
* 📚 Multiple **genres and subgenres**
* 🎭 Dynamic **NPC tracking**
* 📊 Player **stats and morality**
* 🎒 Inventory system *(in development)*
* ✏️ Custom player choices *(optional)*
* ⚙️ Customizable story settings
* 🌡️ Adjustable AI temperature
* 📖 Adjustable passage length
* 💾 Story caching
* 🖥️ Runs directly in the terminal

---

## 🎮 How It Works

The game generates a story based on your chosen genre and your decisions.

Each section of the story gives you several choices.

For example:

```
1. Enter the abandoned laboratory
2. Search the surrounding area
3. Walk away
```

Your decisions are remembered throughout the story, allowing the AI to build on what happened previously.

With **custom choices enabled**, you can also type your own actions instead of selecting one of the generated options.

---

## 🚀 Installation

### Requirements

* Python 3
* An OpenAI API key

### 1. Clone the repository

```
git clone https://github.com/Rueberry1/CYOA_wAI.git
cd CYOA_wAI
```

Alternatively you can download the files from the releases page

### 2. Install dependencies

The program will automatically install the required Python packages when launched.

### 3. Set your API key

Set your `OPENAI_API_KEY` environment variable before running the game.

### 4. Start the game

```
python3 ai_story_generation.py
```

---

## ⚙️ Settings

The game includes several settings that let you customize how stories are generated.

| Setting         | Description                                           |
| --------------- | ----------------------------------------------------- |
| Passage Length  | Controls how long each story segment is               |
| Custom Choices  | Allows you to enter your own actions                  |
| Fourth Wall     | Controls whether the story can acknowledge the player |
| Single Location | Keeps the story within one location                   |
| Profanity       | Controls the amount of profanity                      |
| Violence / Gore | Controls the level of violence                        |
| Romance         | Controls the story's romance focus                    |

---

<details>
<summary>📚 Genres</summary>

The game supports a wide range of genres and subgenres.

Some examples include:

* Science Fiction
* Fantasy
* Horror
* Mystery
* Adventure
* Crime
* Comedy
* Romance
* And more...

</details>

---

## 🧠 How the AI Works

The game uses the OpenAI API to generate story segments based on:

* Your chosen genre
* Previous choices
* Player statistics
* NPC information
* Story settings
* Custom actions

The Python program keeps track of important game state while the AI handles the narrative generation.

---

## 🛠️ Project Structure

```
CYOA_wAI/
├── ai_story_generation.py
├── ai_story_generation_core.py
├── ai_story_generation_ui.py
├── ai_story_generation_settings.py
├── ai_story_generation_genres.py
├── story_cache.json
└── README.md
```

---

## 📸 Screenshots

*Screenshots coming soon!*

---

## 🤖 AI-Assisted Development

I use AI as a programming and learning tool while developing this project.

Parts of the code were created or improved with the help of AI, but I am actively learning and experimenting with the code myself.

---

## 📄 License

Licensed Under **MIT**

---

⭐ If you find this project interesting, feel free to check it out!
