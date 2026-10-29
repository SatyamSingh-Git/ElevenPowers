# recipebox reference

The facts below are what recipebox promises. Each row names the surface it
belongs to: the command line (CLI), the Python API, or a file.

Placeholders in messages are written `{like_this}`. The command line prints
every error as `error: {message}` on stderr.

## Command line

| key | value | meaning |
|---|---|---|
| `home.default` | `~/.recipebox` | home used when neither `--home` nor `$RECIPEBOX_HOME` is given (CLI) |
| `home.variable` | `RECIPEBOX_HOME` | environment variable naming the home (CLI) |
| `error.format` | `error: {message}` | how the CLI prints an error, on stderr (CLI) |
| `exit.error` | `1` | exit status after an error (CLI) |
| `exit.usage` | `2` | exit status after a usage mistake (CLI) |
| `show --servings` | `as written` | default for `show --servings`: the recipe's own servings (CLI) |
| `search --limit` | `10` | default number of matches `search` prints (CLI) |
| `search.more` | `showing {shown} of {total} matches` | printed after the matches when some were left out (CLI) |
| `search.none` | `no recipes match` | printed when nothing matches (CLI) |
| `search.weights` | `title 3, tag 2, ingredient 1` | score a query word earns for each place it is found; best score first, then title (API and CLI) |
| `shop --aisle` | `all aisles` | default for `shop --aisle` (CLI) |
| `shop --csv` | `off` | default for `shop --csv`; with a file, the list is written there instead of printed (CLI) |
| `cookable --missing` | `0` | default number of ingredients `cookable` lets a recipe lack (CLI) |
| `plan.check.weekday_minutes` | `60` | `plan check` warns about a weekday dinner taking longer than this (CLI) |

## Error messages

| key | value | meaning |
|---|---|---|
| `error.unknown_recipe` | `no recipe with id {id}` | `RecipeNotFound` (API, CLI) |
| `error.duplicate_recipe` | `recipe {id} already exists` | `DuplicateRecipe` (API, CLI) |
| `error.unknown_unit` | `unknown unit {unit}` | `UnitError` for a unit recipebox does not know (API, CLI) |
| `error.convert` | `cannot convert {source} to {target}` | `UnitError` between unrelated units (API, CLI) |
| `error.amount` | `cannot read amount {text}` | `AmountError` (API, CLI) |
| `error.servings` | `servings must be between 1 and 100` | `RecipeError` for servings out of range (API, CLI) |
| `error.no_name` | `ingredient has no name: {line}` | `RecipeError` for an ingredient line with no name (API, CLI) |
| `error.recipe_field` | `{file} line {number}: unknown field {field}` | unknown header in a recipe text file (API, CLI) |
| `error.recipe_missing` | `{file}: missing {field}` | recipe text file without `title` or `servings` (API, CLI) |
| `error.plan_line` | `plan line {number}: expected "<day> <meal>: <title>"` | unreadable plan line (API, CLI) |
| `error.plan_day` | `plan line {number}: unknown day {day}` | plan line naming no day of the week (API, CLI) |
| `error.plan_meal` | `plan line {number}: unknown meal {meal}` | plan line naming no known meal (API, CLI) |
| `error.plan_recipe` | `plan line {number}: no recipe titled {title}` | plan line naming a recipe the library lacks (API, CLI) |
| `error.pantry_header` | `{file}: expected the header item,amount,unit` | `pantry.csv` with another header (API, CLI) |
| `error.pantry_missing` | `{item} is not in the pantry` | using or removing what the pantry lacks (API, CLI) |
| `error.bundle` | `{file}: not a recipebox bundle` | importing a file that is not a bundle (API, CLI) |
| `error.bundle_amount` | `recipe {number}, ingredient {number}: cannot read amount {amount}` | bundle ingredient with an amount that cannot be read (API, CLI) |
| `error.search_limit` | `--limit must be at least 1` | `search --limit` below the allowed range (CLI) |

## Limits

| key | value | meaning |
|---|---|---|
| `servings.min` | `1` | fewest servings a recipe, plan line or scale may have (API, CLI) |
| `servings.max` | `100` | most servings a recipe, plan line or scale may have (API, CLI) |
| `title.max` | `80` | longest recipe title, in characters (API, CLI) |
| `tags.max` | `10` | most tags on one recipe (API, CLI) |
| `time.max` | `1440` | longest recipe time, in minutes (API, CLI) |
| `scaling.count_step` | `1/2` | counted ingredients (eggs, cloves, cans) are rounded up to this when scaled (API, CLI) |
| `plan.days` | `monday, tuesday, wednesday, thursday, friday, saturday, sunday` | days a plan line may name (file) |
| `plan.meals` | `breakfast, lunch, dinner, snack` | meals a plan line may name, in the order a day lists them (file) |

## Units and display

| key | value | meaning |
|---|---|---|
| `unit.cup` | `236.588 ml` | one cup (API, CLI) |
| `unit.tbsp` | `14.7868 ml` | one tablespoon (API, CLI) |
| `unit.tsp` | `4.92892 ml` | one teaspoon (API, CLI) |
| `unit.oz` | `28.3495 g` | one ounce (API, CLI) |
| `unit.lb` | `453.592 g` | one pound (API, CLI) |
| `unit.count` | `clove, can, slice` | count units besides a plain count; each only adds up with itself (API, CLI) |
| `display.denominators` | `2, 4, 8` | fractions a non-metric amount is rounded to when shown (CLI) |
| `display.smallest` | `1/8` | shown instead of a non-metric amount that rounds to nothing (CLI) |
| `display.g_ml` | `whole numbers` | how g and ml amounts are shown (CLI) |
| `display.kg_l` | `2 decimal places` | most decimals shown for kg and l, trailing zeros dropped (CLI) |

## Recipe ids

| key | value | meaning |
|---|---|---|
| `recipe.id.characters` | `any except space` | characters a recipe id, made from its title, may contain (CLI) |
| `recipe.id.separator` | `-` | what stands between the words of a title in its id (CLI) |
| `recipe.id.case` | `lower` | case of a recipe id (CLI) |

## Shopping lists

| key | value | meaning |
|---|---|---|
| `shopping.order` | `aisle, name` | order of the lines `build_shopping_list()` returns (API) |
| `aisles` | `produce, bakery, dairy, meat, pantry, frozen, other` | aisle codes in the order the shop is walked; the `aisle` of each `build_shopping_list()` line (API) |
| `shopping.metric_upgrade` | `1000` | g or ml at which a line is given in kg or l (API, CLI) |
| `shopping.empty` | `Nothing to buy.` | printed for an empty list (CLI) |
| `shopping.title` | `Shopping list: {count} items` | first line of the printed list (CLI) |
| `shopping.printed` | `one heading per aisle, in walking order` | how `shop` groups the printed list; items by name under each heading (CLI) |
| `shopping.csv.columns` | `item,quantity,unit` | header of the file `shop --csv` writes (file) |

`pantry restock FILE` reads a list saved with `shop --csv` and adds every
line to the pantry.

## Nutrition

| key | value | meaning |
|---|---|---|
| `nutrition.fields` | `kcal, protein_g, fat_g, carbs_g` | keys of `per_serving` in the summary `nutrition_for()` returns, in order (API) |
| `nutrition.basis` | `per serving` | what `nutrition_for()` values are for (API) |
| `nutrition.kcal.decimals` | `0` | decimals kept for `kcal` (API) |
| `nutrition.grams.decimals` | `1` | decimals kept for every gram value (API) |
| `nutrition.default_density` | `1.0` | g per ml assumed for a liquid the composition table has no density for (API) |

## Files

| key | value | meaning |
|---|---|---|
| `library.file` | `library.json` | the library, in the home (file) |
| `library.version` | `1` | `version` field of `library.json` (file) |
| `library.backup` | `library.json.bak` | the previous library, kept on every save (file) |
| `ingredients[].amount` | `string` | JSON type of an ingredient amount in `library.json`, such as `"1 1/2"`; null when the ingredient has none (file) |
| `ingredients[].unit` | `unit symbol` | an ingredient's unit in `library.json`; empty for a plain count (file) |
| `pantry.csv.columns` | `item,amount,unit` | header of `pantry.csv`; a blank amount marks a staple (file) |
| `bundle.marker` | `recipebox` | key holding the bundle version in an export bundle; its recipes are in the `library.json` form (file) |
| `bundle.version` | `1` | bundle version written by `export` (file) |
| `recipe.separator` | `---` | line between recipes in one recipe text file (file) |
| `[shopping] use_pantry` | `yes` | default in `recipebox.ini`: subtract the pantry when shopping (file) |
| `[plan] meals` | `dinner` | default in `recipebox.ini`: meals `plan suggest` fills (file) |
