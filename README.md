# Nine Men's Morris (Mill) — Python Tkinter

## Overview
This is a local implementation of Nine Men's Morris with a Tkinter Canvas GUI. Options: Play vs AI or Play vs Player.

## Installation & Run

There are two convenient ways to install dependencies and run the game: an automated script included in the repository, or manual commands if you prefer to run the steps yourself.

### Automatic installation & launching

Use the provided helper script to create a virtual environment, install dependencies from `requirements.txt`, and run the application.

- On macOS / Linux / WSL / Git Bash:

```sh
chmod +x start-nine-men-morris.sh
./start-nine-men-morris.sh
```

- On Windows (PowerShell or Git Bash):

```powershell
# If using PowerShell or Git Bash you can run:
./start-nine-men-morris.sh
# Or via bash if available:
bash start-nine-men-morris.sh
```

The script (`start-nine-men-morris.sh`) will:
- detect a usable Python 3 interpreter
- create a `.venv` virtual environment (if missing)
- activate the venv and install packages from `requirements.txt`
- launch the app at `src/main.py`

If you prefer not to run the script, see the manual steps below.

### Manual installation & launching

Run the following commands from the project root to set up a virtual environment and start the game manually.

- Create virtual environment:

```sh
python -m venv .venv
```

- Activate the virtual environment:

On Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
# or
.\.venv\Scripts\activate
```

On Windows (cmd):

```cmd
.\.venv\Scripts\activate.bat
```

On macOS / Linux / WSL:

```sh
source .venv/bin/activate
```

- Install dependencies:

```sh
pip install -r requirements.txt
```

- Run the application:

```sh
python src/main.py
# or on Windows if you prefer
py -3 src/main.py
```

## Notes
- AI uses a shallow minimax with alpha-beta. Increase the search `depth` in `AIPlayer` for stronger play.
- Rules implemented: placing phase (18 pieces), moving phase, mills detection, capture rules, flying when 3 pieces remain.

## Files of interest
- Script: [start-nine-men-morris.sh](start-nine-men-morris.sh)
- Entry point: [src/main.py](src/main.py)
- Requirements: [requirements.txt](requirements.txt)

---

## License & Contribution

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

**Mihai Sirbu**

- GitHub: [Prime-Shadow](https://github.com/Prime-Shadow)
- Email: mihaisirbu28@gmail.com

---