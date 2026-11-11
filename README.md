# PyDave

2D platformer built with Pygame. Run commands from the project root.

## Setup and run

Requires Python 3.11.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The `.venv` is local to this checkout. Do not install the project's packages into system Python.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Pillow and Requests are also used by the asset preparation utilities in the repository.
