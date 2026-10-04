"""Fresh generalized ImpactGraph API, usable independently of a coding agent."""
from .build import build
from .model import Edge, Graph, Node

__all__ = ['build', 'Edge', 'Graph', 'Node']
