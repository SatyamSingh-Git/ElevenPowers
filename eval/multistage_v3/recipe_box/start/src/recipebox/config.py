"""Where recipebox keeps its files, and the settings in `recipebox.ini`."""
import configparser
from dataclasses import dataclass, field
import os
from pathlib import Path

from .core.plan import MEALS
from .errors import RecipeBoxError

DEFAULT_HOME = "~/.recipebox"
HOME_VARIABLE = "RECIPEBOX_HOME"


@dataclass(frozen=True)
class Home:
    root: Path

    @property
    def library(self):
        return self.root / "library.json"

    @property
    def pantry(self):
        return self.root / "pantry.csv"

    @property
    def settings(self):
        return self.root / "recipebox.ini"


def find_home(option=None, environ=os.environ):
    """`--home` if given, else $RECIPEBOX_HOME, else ~/.recipebox."""
    chosen = option or environ.get(HOME_VARIABLE) or DEFAULT_HOME
    return Home(Path(chosen).expanduser())


@dataclass(frozen=True)
class Settings:
    use_pantry: bool = True
    suggest_meals: tuple = field(default=("dinner",))


def load_settings(path):
    """Settings from `path`; a missing file gives the defaults."""
    parser = configparser.ConfigParser()
    if not Path(path).is_file():
        return Settings()
    try:
        parser.read(path, encoding="utf-8")
        use_pantry = parser.getboolean("shopping", "use_pantry", fallback=Settings.use_pantry)
    except (configparser.Error, ValueError) as error:
        raise RecipeBoxError(f"{path}: {error}") from error
    meals = parser.get("plan", "meals", fallback=None)
    suggest_meals = Settings().suggest_meals
    if meals is not None:
        suggest_meals = tuple(meal.strip() for meal in meals.split(",") if meal.strip())
        unknown = [meal for meal in suggest_meals if meal not in MEALS]
        if unknown or not suggest_meals:
            raise RecipeBoxError(f"{path}: [plan] meals must be some of {', '.join(MEALS)}")
    return Settings(use_pantry=use_pantry, suggest_meals=suggest_meals)
