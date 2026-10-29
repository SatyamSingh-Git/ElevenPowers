"""Library statistics as `recipebox stats` prints them."""


def render_stats(stats):
    out = [f"recipes      {stats.recipes}"]
    if stats.average_minutes is not None:
        out.append(f"average time {stats.average_minutes} min over {stats.timed} timed recipes")
        out.append(f"quickest     {stats.quickest.title} ({stats.quickest.minutes} min)")
    if stats.common_ingredients:
        out.append("ingredients  " + ", ".join(f"{name} ({count})" for name, count in stats.common_ingredients))
    if stats.common_tags:
        out.append("tags         " + ", ".join(f"{tag} ({count})" for tag, count in stats.common_tags))
    return "\n".join(out) + "\n"
