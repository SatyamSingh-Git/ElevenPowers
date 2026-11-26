"""What an arm adds to a sealed run's workspace, shared by the held-out and multi-stage runners."""
SUPERPOWERS = 'superpowers@claude-plugins-official'
PROJECT_SETTINGS = {
    'enabledPlugins': {SUPERPOWERS: True},
    'extraKnownMarketplaces': {'claude-plugins-official': {
        'source': {'source': 'github', 'repo': 'anthropics/claude-plugins-official'}}},
}
# The start of ElevenPowers' SessionStart context; superpowers' own says "You have superpowers".
MARK = 'ElevenPowers active'
# Superpowers works through the Skill tool, which the held-out launcher's list leaves out.
TOOLS = 'Bash,Read,Edit,Write,Glob,Grep,Skill'
# A print-mode turn cannot be answered, and a request that stops to ask leaves its stage undone.
UNATTENDED = ("I won't be around to answer questions while you work on this, so make any decisions "
              "yourself and finish the request in this turn.")
# The held-out instructed arm's whole CLAUDE.md.
INSTRUCTION = 'Add a test that fails without your change.'
