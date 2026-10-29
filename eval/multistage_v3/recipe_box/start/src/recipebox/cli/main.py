"""The `recipebox` command line."""
import argparse
from pathlib import Path
import sys

from .. import __version__
from ..config import find_home
from ..core.catalog import AISLE_ORDER
from ..core.plan import DAYS, MEALS
from . import commands

SEARCH_LIMIT = 10


def _positive(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f"{text} is not a positive whole number")
    return value


def build_parser():
    parser = argparse.ArgumentParser(prog="recipebox", description="Recipes, meal plans and shopping lists.")
    parser.add_argument("--version", action="version", version=f"recipebox {__version__}")
    parser.add_argument("--home", help="where the library and pantry live (default: $RECIPEBOX_HOME or ~/.recipebox)")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    add = sub.add_parser("add", help="add recipe text files to the library")
    add.add_argument("files", nargs="+", type=Path)
    add.add_argument("--replace", action="store_true", help="replace a recipe with the same id")
    add.set_defaults(handler=commands.add)

    sub.add_parser("list", help="list the library").set_defaults(handler=commands.list_recipes)

    show = sub.add_parser("show", help="print a recipe")
    show.add_argument("id")
    show.add_argument("--servings", type=_positive, help="scale to this many servings")
    show.add_argument("--use", metavar="AMOUNT", help='scale to use up an amount, for example "500 g macaroni"')
    show.add_argument("--markdown", action="store_true", help="print Markdown")
    show.add_argument("--html", action="store_true", help="print a printable HTML page")
    show.set_defaults(handler=commands.show)

    dump = sub.add_parser("dump", help="print a recipe as recipe text, ready to edit and add again")
    dump.add_argument("id")
    dump.add_argument("--servings", type=_positive, help="scale to this many servings")
    dump.set_defaults(handler=commands.dump)

    listed = sub.add_parser("ingredients", help="every ingredient in the library, with how many recipes use it")
    listed.add_argument("--by-aisle", action="store_true", help="group the ingredients by aisle instead")
    listed.set_defaults(handler=commands.ingredients)
    uses = sub.add_parser("uses", help="recipes that use an ingredient")
    uses.add_argument("ingredient", nargs="+")
    uses.set_defaults(handler=commands.uses)

    sub.add_parser("tags", help="list tags and how many recipes carry each").set_defaults(handler=commands.tags)

    rename = sub.add_parser("rename", help="give a recipe a new title (and so a new id)")
    rename.add_argument("id")
    rename.add_argument("title")
    rename.set_defaults(handler=commands.rename)

    remove = sub.add_parser("remove", help="remove a recipe from the library")
    remove.add_argument("id")
    remove.set_defaults(handler=commands.remove)

    find = sub.add_parser("search", help="find recipes by title, tag or ingredient")
    find.add_argument("words", nargs="*")
    find.add_argument("--tag")
    find.add_argument("--max-time", type=_positive, metavar="MINUTES")
    find.add_argument("--limit", type=int, default=SEARCH_LIMIT, help=f"most matches to show (default {SEARCH_LIMIT})")
    find.set_defaults(handler=commands.find)

    nutrition = sub.add_parser("nutrition", help="nutrition per serving")
    nutrition.add_argument("id")
    nutrition.set_defaults(handler=commands.nutrition)

    shop = sub.add_parser("shop", help="shopping list for a meal plan")
    shop.add_argument("plan", type=Path)
    shop.add_argument("--csv", type=Path, metavar="FILE", help="write the list as CSV instead of printing it")
    shop.add_argument("--no-pantry", action="store_true", help="ignore what the pantry holds")
    shop.add_argument("--aisle", choices=AISLE_ORDER, help="only this aisle")
    shop.add_argument("--markdown", action="store_true", help="print a Markdown checklist")
    shop.set_defaults(handler=commands.shop)

    plan = sub.add_parser("plan", help="meal plans").add_subparsers(dest="action", required=True, metavar="ACTION")
    plan_show = plan.add_parser("show", help="print a plan")
    plan_show.add_argument("plan", type=Path)
    plan_show.add_argument("--energy", action="store_true", help="add each day's energy per person")
    plan_show.add_argument("--grid", action="store_true", help="print the week as a grid")
    plan_show.set_defaults(handler=commands.plan_show)
    plan_check = plan.add_parser("check", help="point out repeats, gaps and long weekday dinners")
    plan_check.add_argument("plan", type=Path)
    plan_check.set_defaults(handler=commands.plan_check)
    plan_nutrition = plan.add_parser("nutrition", help="nutrition per person for each planned day")
    plan_nutrition.add_argument("plan", type=Path)
    plan_nutrition.set_defaults(handler=commands.plan_nutrition)
    suggest = plan.add_parser("suggest", help="suggest a week from the library")
    suggest.add_argument("--meal", action="append", choices=MEALS, help="meal to plan; repeat for more")
    suggest.add_argument("--tag")
    suggest.add_argument("--out", type=Path, metavar="FILE")
    suggest.set_defaults(handler=commands.plan_suggest)
    plan_set = plan.add_parser("set", help="set one meal of a plan file")
    plan_set.add_argument("plan", type=Path)
    plan_set.add_argument("day", choices=DAYS)
    plan_set.add_argument("meal", choices=MEALS)
    plan_set.add_argument("id")
    plan_set.add_argument("--servings", type=_positive)
    plan_set.set_defaults(handler=commands.plan_set)
    prep = plan.add_parser("prep", help="the chopping, grating and so on a plan needs, all together")
    prep.add_argument("plan", type=Path)
    prep.set_defaults(handler=commands.plan_prep)
    calendar = plan.add_parser("calendar", help="write the plan as an iCalendar file")
    calendar.add_argument("plan", type=Path)
    calendar.add_argument("--week-of", required=True, metavar="YYYY-MM-DD", help="the Monday the week starts")
    calendar.add_argument("--out", required=True, type=Path, metavar="FILE")
    calendar.set_defaults(handler=commands.plan_calendar)

    pantry = sub.add_parser("pantry", help="what is in the kitchen").add_subparsers(
        dest="action", required=True, metavar="ACTION")
    pantry.add_parser("list").set_defaults(handler=commands.pantry_list)
    pantry_add = pantry.add_parser("add", help="add an item; without a quantity it is a staple")
    pantry_add.add_argument("item")
    pantry_add.add_argument("quantity", nargs="*")
    pantry_add.set_defaults(handler=commands.pantry_add)
    pantry_use = pantry.add_parser("use", help="take some of an item out")
    pantry_use.add_argument("item")
    pantry_use.add_argument("quantity", nargs="+")
    pantry_use.set_defaults(handler=commands.pantry_use)
    pantry_remove = pantry.add_parser("remove")
    pantry_remove.add_argument("item")
    pantry_remove.set_defaults(handler=commands.pantry_remove)
    restock = pantry.add_parser("restock", help="add everything on a shopping list saved with shop --csv")
    restock.add_argument("file", type=Path)
    restock.set_defaults(handler=commands.pantry_restock)

    cook = sub.add_parser("cookable", help="recipes the pantry can cook")
    cook.add_argument("--missing", type=int, default=0, metavar="N", help="allow up to N missing ingredients")
    cook.set_defaults(handler=commands.what_can_i_cook)

    convert = sub.add_parser("convert", help="convert an amount of an ingredient to another unit")
    convert.add_argument("quantity", help='for example "2 cup"')
    convert.add_argument("ingredient", nargs="+")
    convert.add_argument("--to", required=True, metavar="UNIT")
    convert.set_defaults(handler=commands.convert)

    swap = sub.add_parser("substitute", help="what can stand in for an ingredient")
    swap.add_argument("item")
    swap.add_argument("quantity", nargs="*")
    swap.set_defaults(handler=commands.swap)

    sub.add_parser("stats", help="library statistics").set_defaults(handler=commands.stats)

    export = sub.add_parser("export", help="write recipes to a bundle")
    export.add_argument("out", type=Path)
    export.add_argument("ids", nargs="*", help="recipes to export (default: all)")
    export.set_defaults(handler=commands.export)

    bring = sub.add_parser("import", help="add the recipes of a bundle")
    bring.add_argument("bundle", type=Path)
    bring.add_argument("--replace", action="store_true", help="replace recipes the library already has")
    bring.set_defaults(handler=commands.import_)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return commands.run(args.handler, args, find_home(args.home))


if __name__ == "__main__":
    sys.exit(main())
