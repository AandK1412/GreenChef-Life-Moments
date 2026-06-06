# Contributing

Thanks for your interest in the project.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Before opening a PR

```bash
make test     # all tests must pass, including the 50-case regression gate
make lint     # ruff
```

## The regression gate

`tests/test_regression.py` enforces the report's deployment rule (Appendix M):
any change to the classification logic or prompt may ship only if it
misclassifies **at most 3 of the 50** golden cases in
`tests/fixtures/regression_cases.json`. If you change the prompt or heuristic,
run the suite and, if you intend to change expected behaviour, update the
fixture deliberately in the same PR.

## Adding a backend

Implement the `Classifier` protocol (`name` attribute + `classify(comment) ->
Classification`) and register it in `get_classifier()`.

## Conventions

- Keep modules small and single-purpose; mirror report sections where practical.
- New behaviour needs a test.
- No real subscriber data, ever — synthetic only (see `data/README.md`).
