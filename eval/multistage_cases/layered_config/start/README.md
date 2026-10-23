# layercfg

Loads the application's configuration from three layers, each overriding the
one before: built-in defaults, an INI file, and environment variables. Every
value is coerced to its option's type and checked against its range; every
problem in every layer is reported at once.

```python
from layercfg import load

config = load(open('app.ini').read(), env=dict(os.environ), file_name='app.ini')
config['server.port']          # 8080
config.source('server.port')   # 'app.ini line 3'
```

```
python -m layercfg.cli dump --format sources --config app.ini
python -m layercfg.cli explain server.port
```

Run the suite with `python -m pytest`. Facts about behaviour live in
`docs/reference.md`.
