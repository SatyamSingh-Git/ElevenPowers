# Changelog

## Unreleased

- `plan check` points out repeated recipes, empty days and long weekday dinners.

## 0.9.0

- `ingredients` and `uses` show which recipes use what.
- `show --use "500 g macaroni"` scales a recipe to use up an amount.
- `substitute` suggests stand-ins for buttermilk, cream, eggs and a few others.
- The library keeps the previous `library.json` as `library.json.bak` on every save.

## 0.8.0

- `pantry restock` adds a list saved with `shop --csv` to the pantry.
- `plan nutrition` prints each planned day's nutrition per person.
- `export` and `import` move recipes between libraries as bundles.
- `plan prep` gathers the chopping, grating and melting a plan needs; `plan calendar` writes the week as an iCalendar file.
- `show --html` prints a recipe as a printable page.
