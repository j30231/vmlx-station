# Contributing

## Principles

- keep the runtime layer thin and operationally clear
- keep backend-specific behavior inside the runtime integration layer
- prefer small, testable surfaces over implicit magic

## Development flow

1. open an issue or write a short problem statement
2. keep changes scoped to one layer when possible
3. verify both:
   - daemon behavior
   - menu bar build or behavior
4. update docs when behavior changes

## Local checks

```bash
python3 -m compileall runtime/src
cd runtime && source .venv/bin/activate && pip install -e .
cd .. && swift build
```

