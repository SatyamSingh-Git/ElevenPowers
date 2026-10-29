"""Bringing records in from other systems.

Importers build model records and hand them to a `Fleet`; they do not go
through the command-line services, so one bad row never half-applies a command.
"""
