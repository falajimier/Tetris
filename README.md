# Tetris

A classic  Tetris –style game written in Python, rendered with **OpenGL** through Pygame. 



## Features

- 🎮 Smooth OpenGL-accelerated 2D rendering (1260×800, 60 FPS)
  - 🔊 Procedurally generated sound effects
- 🎵 Optional background music — just drop an MP3 file (`music.mp3`, `background.mp3`, `game_music.mp3`, `soundtrack.mp3`) next to the script
- ⏸️ Pause menu and level-select

## Requirements

- Python 3.8+
- [Pygame](https://www.pygame.org/)
- [PyOpenGL](http://pyopengl.sourceforge.net/)
- [NumPy](https://numpy.org/)
- [OpenCV (opencv-python)](https://pypi.org/project/opencv-python/)

Install the dependencies:

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy opencv-python
```

## Running the Game

```bash
python tetris9k.py
```

## Controls

| Key | Action |
|-----|--------|
| ← / → | Move figure |
| ↑     | Rotate figure |
| SPACE | Drop figure down |
| Enter | Confirm menu selection |
| Esc | Pause / open menu |
| M | Toggle background music |
| R | Restart after game over or victory |


Paddle guns (once activated by a red brick) fire automatically.

## Adding Background Music

The game looks for one of the following files in the working directory and plays it on loop if found:

music.mp3
background.mp3
game_music.mp3
soundtrack.mp3


If none are present, the game runs silently for music (sound effects still play, as they are generated procedurally).

## Project Structure


tetris9k.py    # Single-file game


## License

No license specified yet — add one (e.g., MIT) if you plan to share or accept contributions.
