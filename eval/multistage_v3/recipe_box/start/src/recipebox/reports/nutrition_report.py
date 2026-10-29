"""The nutrition summary as `recipebox nutrition` prints it."""

# Summary key -> (label, unit shown after the value).
LABELS = {
    "kcal": ("Energy", "kcal"),
    "protein_g": ("Protein", "g"),
    "fat_g": ("Fat", "g"),
    "carbs_g": ("Carbohydrate", "g"),
}


def render_nutrition(summary):
    out = [f"{summary.title}, per serving (serves {summary.servings})"]
    for key, value in summary.per_serving.items():
        label, unit = LABELS[key]
        out.append(f"  {label:<14}{value:>7} {unit}")
    if summary.missing:
        out.append(f"Not counted: {', '.join(summary.missing)}")
    return "\n".join(out) + "\n"
