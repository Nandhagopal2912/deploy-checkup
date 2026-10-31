# deploy-checkup

[![CI](https://github.com/Nandhagopal2912/deploy-checkup/actions/workflows/ci.yml/badge.svg)](https://github.com/Nandhagopal2912/deploy-checkup/actions/workflows/ci.yml)

Tells you, in plain language, whether your deployed app is set up safely, and exactly how to fix what isn't on your host.

> **Only test apps you own or have permission to test.** Against someone else's site, unusual requests can look like an attack and may be illegal.

## Status

Early development (`0.0.1`, not yet on PyPI). CI runs the tests on Python 3.10 and 3.13.

| Check | Runs on | What it asks |
|---|---|---|
| **reachable** | frontend | Does the address answer, and with what status? |
| **https** | frontend and API | Does plain `http://` redirect to `https://`, and permanently (301/308)? |
| **headers** | frontend | Are the browser security headers set? Strict-Transport-Security (at least 6 months), X-Content-Type-Options (`nosniff`), Content-Security-Policy, X-Frame-Options (or CSP `frame-ancestors`), Referrer-Policy |

The headers check skips the API on purpose: a JSON API doesn't need CSP or X-Frame-Options, and flagging them would be a false alarm.

Still to come for version 1: CORS behaviour, health and latency, cold start, and exposed files. Fix hints target Render first. See the [roadmap](docs/Deploy%20Doctor%20Roadmap.pdf).

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

Example output:

```
──────────── https://your-frontend.onrender.com ────────────
PASS    Site answered with status 200
PASS    Plain HTTP redirects to HTTPS (301)
WARNING Content-Security-Policy is missing
        Why: If an attacker manages to inject a script into your page, the browser will run it. ...
        Fix: Start with Content-Security-Policy: default-src 'self' and loosen it ...

Summary: 6 pass, 1 warning, 0 fail, 0 info
```

Each finding says what was found, why it matters, and how to fix it. The command exits with code `1` if anything fails, so you can run it in CI after a deploy, and `0` otherwise.

Every request uses a 60-second timeout (Render's free tier can take about 50 seconds to wake up) and identifies itself as `User-Agent: DeployCheckup/<version>`.

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

`-e` installs in editable mode, so code changes take effect without reinstalling. Re-run the install after changing `dependencies` or `[project.scripts]` in `pyproject.toml`.

## Running tests

```bash
pytest
```

Tests never touch the network. Each check receives an `httpx.Client`, and tests pass one built on `httpx.MockTransport`, which answers requests with fake responses.

## License

[MIT](LICENSE)
