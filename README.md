# deploy-checkup

[![CI](https://github.com/Nandhagopal2912/deploy-checkup/actions/workflows/ci.yml/badge.svg)](https://github.com/Nandhagopal2912/deploy-checkup/actions/workflows/ci.yml)

Tells you, in plain language, whether your deployed app is set up safely, and exactly how to fix what isn't on your host.

> **Only test apps you own or have permission to test.** Against someone else's site, unusual requests can look like an attack and may be illegal.

## Install

Requires Python 3.10 or newer.

```bash
pipx install deploy-checkup
```

`pipx` installs command-line tools in their own environment. `pip install deploy-checkup` works too.

## Usage

```bash
deploy-checkup https://your-frontend.onrender.com --api https://your-api.onrender.com
```

| Option | Meaning |
|---|---|
| `url` | Your frontend's address (required) |
| `--api` | Your API's address, if it is separate |
| `--health-path` | The API's health check path (default `/health`) |
| `--yes-i-own-it` | Run the probing checks without asking (for CI) |
| `--json` | Print the findings as JSON instead of a coloured report |
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

## What it checks

| Check | Runs on | What it asks |
|---|---|---|
| **reachable** | frontend | Does the address answer, and with what status? |
| **https** | frontend and API | Does plain `http://` redirect to `https://`, and permanently (301/308)? |
| **headers** | frontend | Are the browser security headers set? Strict-Transport-Security (at least 6 months), X-Content-Type-Options (`nosniff`), Content-Security-Policy, X-Frame-Options (or CSP `frame-ancestors`), Referrer-Policy |
| **cors** | API | Asks the API as your frontend, then as a made-up site (`deploy-checkup-test.invalid`). Is your frontend allowed and everyone else blocked? |
| **health** | API | Calls the health path 3 times. Does it exist, and what's the median response time? |
| **cold_start** | API | Was the first of those requests much slower than the rest (a free tier waking up)? Reported as a hint, not a verdict. |
| **exposed_files** | frontend and API | Can anyone download `/.env` or `/.git/config`? **Probing:** runs only after you confirm you own the site. |

The headers check skips the API on purpose: a JSON API doesn't need CSP or X-Frame-Options, and flagging them would be a false alarm.

**Fix hints match your host.** When a response carries Render's `x-render-origin-server` header, fixes point to the exact place in the Render dashboard. On any other host you get general advice.

### Probing checks ask first

Most checks send ordinary requests any browser could send. The exposed files check asks for paths like `/.env`, which on someone else's site can look like an attack. So deploy-checkup asks *"Do you own this site?"* before running it. If nobody can answer (in CI, for example), it is skipped and the report says so, unless you pass `--yes-i-own-it`. A leaked file's contents are never shown in the report.

### Polite by design

Every request uses a 60-second timeout (Render's free tier can take about 50 seconds to wake up) and identifies itself as `User-Agent: DeployCheckup/<version>`, so site owners can see what called them. A full run sends a few dozen ordinary requests.

## JSON output

`--json` prints the same findings for scripts and CI. Only the JSON goes to standard output; the permission question goes to standard error, so you can save the report safely:

```bash
deploy-checkup https://your-frontend.onrender.com --api https://your-api.onrender.com --json > report.json
```

```json
{
  "tool": "deploy-checkup",
  "version": "0.1.0",
  "targets": [
    {
      "url": "https://your-api.onrender.com",
      "findings": [
        {"check": "health", "level": "pass", "title": "API answered in 108 ms (median of 2)", "why": "", "fix": ""}
      ]
    }
  ],
  "summary": {"pass": 16, "warning": 0, "fail": 0, "info": 0}
}
```

The exit code is the same as for the coloured report.

## Development

```bash
git clone https://github.com/Nandhagopal2912/deploy-checkup.git
cd deploy-checkup
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

`-e` installs in editable mode, so code changes take effect without reinstalling. Re-run the install after changing `dependencies` or `[project.scripts]` in `pyproject.toml`.

Tests never touch the network. Each check receives an `httpx.Client`, and tests pass one built on `httpx.MockTransport`, which answers requests with fake responses. CI runs them on Python 3.10 and 3.13.

[`demo/`](https://github.com/Nandhagopal2912/deploy-checkup/tree/main/demo) holds a deliberately broken app with known flaws, used to prove each check catches what it should. The project's plan is in the [roadmap](https://github.com/Nandhagopal2912/deploy-checkup/blob/main/docs/Deploy%20Doctor%20Roadmap.pdf).

## License

[MIT](https://github.com/Nandhagopal2912/deploy-checkup/blob/main/LICENSE)
