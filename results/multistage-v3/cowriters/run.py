"""The co-readers evaluation, unchanged, with the same-state scorer swapped in.
Results are written here."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coreaders'))
import cowriters  # noqa: E402
import run as evaluation  # noqa: E402  (coreaders/run.py)

evaluation.scored = cowriters.scored
evaluation.HERE = HERE
evaluation.main()
