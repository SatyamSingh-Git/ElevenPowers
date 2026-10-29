"""What each command does. Each handler takes the parsed arguments and the home, prints, and returns an exit status."""
from dataclasses import replace
import sys

from ..config import load_settings
from ..core.plan import Plan
from ..core.ingredients import Ingredient, canonical_name, describe_ingredient, parse_ingredient
from ..core.quantity import parse_quantity
from ..core.recipe import validate
from ..errors import DuplicateRecipe, RecipeBoxError
from ..reports.markdown import recipe_markdown, shopping_markdown
from ..reports.nutrition_report import render_nutrition
from ..reports.pantry_report import render_pantry
from ..reports.plan_grid import render_grid
from ..reports.plan_report import render_plan
from ..reports.prep_report import render_prep
from ..reports.recipe_card import render_listing, render_recipe
from ..reports.recipe_html import recipe_html
from ..reports.shopping_csv import write_shopping_csv
from ..reports.shopping_text import render_shopping_list
from ..reports.stats_report import render_stats
from ..reports.week_report import render_week
from ..services.conversion import convert_ingredient
from ..services.cookable import cookable
from ..services.importer import import_bundle
from ..services.ingredient_index import ingredient_index, ingredients_by_aisle, recipes_using
from ..services.nutrition import nutrition_for
from ..services.plan_check import check_plan
from ..services.planner import replace_meal, suggest_plan
from ..services.prep import prep_list
from ..services.scaling import scale_recipe, servings_for
from ..services.search import search
from ..services.shopping import build_shopping_list
from ..services.stats import library_stats
from ..services.substitutes import substitute
from ..services.weekly import daily_average, week_intake
from ..storage.bundle import write_bundle
from ..storage.library import Library
from ..storage.pantry_file import load_pantry, read_purchases, save_pantry
from ..storage.plan_calendar import parse_week, save_calendar
from ..storage.plan_file import format_plan, load_plan, parse_plan, save_plan
from ..storage.recipe_text import dump_recipe, read_recipe_file


def add(args, home):
    library = Library.load(home.library)
    recipes = [recipe for path in args.files for recipe in read_recipe_file(path)]
    for recipe in recipes:
        library.add(recipe, replace=args.replace)
    library.save()
    for recipe in recipes:
        print(f"added {recipe.id}")
    return 0


def list_recipes(args, home):
    print(render_listing(Library.load(home.library)), end="")
    return 0


def show(args, home):
    recipe = Library.load(home.library).get(args.id)
    if args.use:
        have = parse_ingredient(args.use)
        if have.quantity is None:
            raise RecipeBoxError(f"--use needs an amount: {args.use}")
        recipe = scale_recipe(recipe, servings_for(recipe, have.name, have.quantity))
    elif args.servings is not None:
        recipe = scale_recipe(recipe, args.servings)
    if args.html:
        print(recipe_html(recipe), end="")
    else:
        print((recipe_markdown if args.markdown else render_recipe)(recipe), end="")
    return 0


def dump(args, home):
    recipe = Library.load(home.library).get(args.id)
    if args.servings is not None:
        recipe = scale_recipe(recipe, args.servings)
    print(dump_recipe(recipe), end="")
    return 0


def tags(args, home):
    counts = {}
    for recipe in Library.load(home.library):
        for tag in recipe.tags:
            counts[tag] = counts.get(tag, 0) + 1
    for tag in sorted(counts):
        print(f"{tag}  {counts[tag]}")
    return 0


def rename(args, home):
    library = Library.load(home.library)
    recipe = library.get(args.id)
    renamed = replace(recipe, title=args.title.strip())
    validate(renamed)
    if renamed.id != recipe.id and renamed.id in library:
        raise DuplicateRecipe(renamed.id)
    library.remove(recipe.id)
    library.add(renamed)
    library.save()
    print(f"{recipe.id} is now {renamed.id}")
    return 0


def ingredients(args, home):
    library = Library.load(home.library)
    if args.by_aisle:
        for aisle, names in ingredients_by_aisle(library).items():
            print(f"{aisle}: {', '.join(names)}")
        return 0
    for name, titles in ingredient_index(library).items():
        print(f"{name}  ({len(titles)})")
    return 0


def uses(args, home):
    found = recipes_using(Library.load(home.library), " ".join(args.ingredient))
    if not found:
        print("no recipe uses it")
    print(render_listing(found), end="")
    return 0


def remove(args, home):
    library = Library.load(home.library)
    library.remove(args.id)
    library.save()
    print(f"removed {args.id}")
    return 0


def find(args, home):
    if args.limit < 1:
        raise RecipeBoxError("--limit must be at least 1")
    matches = search(Library.load(home.library), " ".join(args.words), tag=args.tag, max_minutes=args.max_time)
    if not matches:
        print("no recipes match")
        return 0
    shown = matches[:args.limit]
    print(render_listing(match.recipe for match in shown), end="")
    if len(shown) < len(matches):
        print(f"showing {len(shown)} of {len(matches)} matches")
    return 0


def nutrition(args, home):
    recipe = Library.load(home.library).get(args.id)
    print(render_nutrition(nutrition_for(recipe)), end="")
    return 0


def shop(args, home):
    library = Library.load(home.library)
    plan = load_plan(args.plan, library)
    settings = load_settings(home.settings)
    pantry = load_pantry(home.pantry) if settings.use_pantry and not args.no_pantry else None
    lines = build_shopping_list(plan, pantry)
    if args.aisle:
        lines = [line for line in lines if line.aisle == args.aisle]
    if args.csv:
        count = write_shopping_csv(lines, args.csv)
        print(f"wrote {count} items to {args.csv}")
    elif args.markdown:
        print(shopping_markdown(lines), end="")
    else:
        print(render_shopping_list(lines), end="")
    return 0


def plan_show(args, home):
    plan = load_plan(args.plan, Library.load(home.library))
    if args.grid:
        print(render_grid(plan), end="")
        return 0
    energy = None
    if args.energy:
        energy = {day.day: round(day.amounts["kcal"]) for day in week_intake(plan)}
    print(render_plan(plan, energy), end="")
    return 0


def plan_nutrition(args, home):
    week = week_intake(load_plan(args.plan, Library.load(home.library)))
    print(render_week(week, daily_average(week)), end="")
    return 0


def plan_check(args, home):
    warnings = check_plan(load_plan(args.plan, Library.load(home.library)))
    for warning in warnings:
        print(f"{warning.day}: {warning.message}")
    if not warnings:
        print("the plan looks fine")
    return 0


def plan_prep(args, home):
    print(render_prep(prep_list(load_plan(args.plan, Library.load(home.library)))), end="")
    return 0


def plan_calendar(args, home):
    monday = parse_week(args.week_of)
    count = save_calendar(load_plan(args.plan, Library.load(home.library)), monday, args.out)
    print(f"wrote {count} meals to {args.out}")
    return 0


def plan_suggest(args, home):
    settings = load_settings(home.settings)
    meals = tuple(args.meal) if args.meal else settings.suggest_meals
    plan = suggest_plan(Library.load(home.library), meals=meals, tag=args.tag)
    if args.out:
        save_plan(plan, args.out)
        print(f"wrote {len(plan)} meals to {args.out}")
    else:
        print(format_plan(plan), end="")
    return 0


def plan_set(args, home):
    library = Library.load(home.library)
    recipe = library.get(args.id)
    plan = parse_plan(args.plan.read_text(encoding="utf-8"), library) if args.plan.is_file() else Plan()
    plan = replace_meal(plan, args.day, args.meal, recipe, args.servings)
    save_plan(plan, args.plan)
    print(f"{args.day} {args.meal}: {recipe.title}")
    return 0


def pantry_list(args, home):
    print(render_pantry(load_pantry(home.pantry)), end="")
    return 0


def pantry_add(args, home):
    pantry = load_pantry(home.pantry)
    quantity = parse_quantity(" ".join(args.quantity)) if args.quantity else None
    item = pantry.add(args.item, quantity)
    save_pantry(pantry, home.pantry)
    print(f"{item.name}: {'staple' if item.staple else item.quantity}")
    return 0


def pantry_use(args, home):
    pantry = load_pantry(home.pantry)
    pantry.use(args.item, parse_quantity(" ".join(args.quantity)))
    save_pantry(pantry, home.pantry)
    held = pantry.get(args.item)
    print(f"{args.item}: {'none left' if held is None else 'staple' if held.staple else held.quantity}")
    return 0


def pantry_remove(args, home):
    pantry = load_pantry(home.pantry)
    pantry.remove(args.item)
    save_pantry(pantry, home.pantry)
    print(f"removed {args.item}")
    return 0


def pantry_restock(args, home):
    pantry = load_pantry(home.pantry)
    count = pantry.restock(read_purchases(args.file))
    save_pantry(pantry, home.pantry)
    print(f"restocked {count} items")
    return 0


def what_can_i_cook(args, home):
    found = cookable(Library.load(home.library), load_pantry(home.pantry), missing=args.missing)
    if not found:
        print("nothing can be cooked from the pantry")
        return 0
    for entry in found:
        short = f"  (needs {', '.join(entry.short)})" if entry.short else ""
        print(f"{entry.recipe.id}{short}")
    return 0


def convert(args, home):
    name = canonical_name(" ".join(args.ingredient))
    converted = convert_ingredient(name, parse_quantity(args.quantity), args.to)
    print(f"{converted} {name}")
    return 0


def swap(args, home):
    quantity = parse_quantity(" ".join(args.quantity)) if args.quantity else None
    replacements, hint = substitute(Ingredient(canonical_name(args.item), quantity))
    for ingredient in replacements:
        print(describe_ingredient(ingredient))
    if hint:
        print(f"({hint})")
    return 0


def stats(args, home):
    print(render_stats(library_stats(Library.load(home.library))), end="")
    return 0


def export(args, home):
    library = Library.load(home.library)
    recipes = [library.get(rid) for rid in args.ids] if args.ids else list(library)
    count = write_bundle(recipes, args.out)
    print(f"exported {count} recipes to {args.out}")
    return 0


def import_(args, home):
    library = Library.load(home.library)
    report = import_bundle(library, args.bundle, replace=args.replace)
    library.save()
    for rid in report.added:
        print(f"added {rid}")
    for rid in report.replaced:
        print(f"replaced {rid}")
    for rid in report.skipped:
        print(f"skipped {rid} (already in the library)")
    return 0


def run(handler, args, home):
    """Run `handler`, turning a RecipeBoxError into `error: ...` on stderr and status 1."""
    try:
        return handler(args, home)
    except RecipeBoxError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
