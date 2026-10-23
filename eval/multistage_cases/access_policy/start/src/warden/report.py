"""Summaries of an audit log."""
from collections import Counter
from dataclasses import dataclass, field

from .audit import read_log

TOP = 5


@dataclass
class Summary:
    total: int = 0
    allowed: int = 0
    denied: int = 0
    # user name -> (allowed, denied)
    users: dict = field(default_factory=dict)
    denied_resources: Counter = field(default_factory=Counter)


def summarize(records):
    summary = Summary()
    for item in records:
        allowed, denied = summary.users.get(item["user"], (0, 0))
        summary.total += 1
        if item["allowed"]:
            summary.allowed += 1
            allowed += 1
        else:
            summary.denied += 1
            denied += 1
            summary.denied_resources[item["resource"]] += 1
        summary.users[item["user"]] = (allowed, denied)
    return summary


def summarize_file(path):
    return summarize(read_log(path))


def format_summary(summary, top=TOP):
    lines = [f"{summary.total} decisions: {summary.allowed} allowed, {summary.denied} denied"]
    if summary.users:
        lines.append("by user:")
        width = max(len(name) for name in summary.users)
        for name in sorted(summary.users):
            allowed, denied = summary.users[name]
            lines.append(f"  {name:<{width}}  {allowed} allowed  {denied} denied")
    if summary.denied_resources:
        lines.append("most denied:")
        for resource, count in summary.denied_resources.most_common(top):
            lines.append(f"  {resource}  {count}")
    return "\n".join(lines)
