# deploy-checkup

[![CI](https://github.com/Nandhagopal2912/deploy-checkup/actions/workflows/ci.yml/badge.svg)](https://github.com/Nandhagopal2912/deploy-checkup/actions/workflows/ci.yml)

Tells you, in plain language, whether your deployed app is set up safely, and exactly how to fix what isn't on your host.

> **Only test apps you own or have permission to test.** Against someone else's site, unusual requests can look like an attack and may be illegal.

## Status

Early development (`0.0.1`). The command-line skeleton works and has tests, which CI runs on Python 3.10 and 3.13. Checks report `Finding` records (check name, level, title, why it matters, how to fix). One placeholder check (is the URL reachable?) exists but isn't connected to the command yet.

Planned for version 1: HTTPS and redirects, security headers, CORS behaviour, health and latency, cold start, and exposed files. Fix hints target Render first. See the [roadmap](docs/Deploy%20Doctor%20Roadmap.pdf).

## Usage

```bash
deploy-checkup https://your-frontend.onrender.com --api https://your-api.onrender.com
```

| Option | Meaning |
|---|---|
| `url` | Your frontend's address (required) |
| `--api` | Your API's address, if it is separate |
| `-V`, `--version` | Show the version |
| `-h`, `--help` | Show help |

## Development setup

Requires Python 3.10 or newer.

```bash
git clone https://github.com/Nandhagopal2912/deploy-checkup.git
cd deploy-checkup
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
deploy-checkup --help
```

`-e` installs in editable mode, so code changes take effect without reinstalling. Re-run the install after changing `[project.scripts]` in `pyproject.toml`.

## Running tests

```bash
pytest
```

Tests never touch the network. Each check receives an `httpx.Client`, and tests pass one built on `httpx.MockTransport`, which answers requests with fake responses.

## License

[MIT](LICENSE)
