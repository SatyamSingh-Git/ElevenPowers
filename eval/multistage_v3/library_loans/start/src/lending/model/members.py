"""Library members."""
from dataclasses import dataclass
from datetime import date
import re

KINDS = ('adult', 'child')
CARD = re.compile(r'[A-Z]\d{4,8}')


@dataclass
class Member:
    card: str
    name: str
    email: str
    kind: str
    born: date
    joined: date


def normalise_card(text):
    return text.strip().upper()


def problems(member):
    """What is wrong with a member record, as short phrases; empty when it is fine."""
    found = []
    if not CARD.fullmatch(member.card):
        found.append('card must be a letter followed by 4 to 8 digits')
    if not member.name.strip():
        found.append('name is empty')
    if member.email and '@' not in member.email:
        found.append(f'email {member.email} has no @')
    if member.kind not in KINDS:
        found.append(f"type {member.kind} is not one of {', '.join(KINDS)}")
    if member.born > member.joined:
        found.append('joined before they were born')
    return found
