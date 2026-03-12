# Run & Gun Side-Scroller Prototype (Pygame-CE)

A small **teaching-friendly** prototype for a first-year *run-and-gun* side-scrolling shooter.

## Features (prototype baseline)
- Start screen + game over screen
- One scrolling tile-based level (CSV)
- Platform collisions, jumping, shooting
- Normal enemies + a boss at the end
- Health pickup
- Basic sprite-sheet animation support (rows/frames)
- Sound effects + looping music (WAV placeholders)

## Controls
- **A/D**: Move
- **W**: Jump
- **Space**: Shoot
- **Enter**: Start / Continue
- **R**: Restart on Game Over
- **Esc**: Quit

## Remove redundant files from git
.gitignore file should stop __pycache__ and .venv from being saved and downloaded every time

You can remove it from your local (and then remote) repository with

```bash
git rm -r --cached __pycache__
git rm -r --cached src\weapons\__pycache__
git commit -m "Remove __pycache__ from repository"
git push 
```

You can do similar with .venv

```bash
deactivate
git rm -r --cached .venv
git commit -m "Remove .venv from repository"
git push 
```

After doing this you will need to recreate your .venv and install the requirements as described below.

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
.venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m src.main
```

If this brings up an error about pygame.base not loading then do the following

```bash
python -m pip uninstall pygame-ce
python -m pip cache purge
python -m pip install pygame-ce
```

## Level tiles (CSV)
Each cell is one tile (32x32).

Legend:

* `00` empty
* `01` Ground
* `02` Platform
* `03` Platform Left Edge
* `04` Platform Right Edge
* `05` Wall
* `90` player spawn
* `91` runner enemy
* `92` health pickup
* `93` boss spawn
* `94` exit
* `95` shooter enemy

Edit: `assets/levels/level1.csv`

