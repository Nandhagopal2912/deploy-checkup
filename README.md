# deploy-checkup

[![CI](https://github.com/Nandhagopal2912/deploy-checkup/actions/workflows/ci.yml/badge.svg)](https://github.com/Nandhagopal2912/deploy-checkup/actions/workflows/ci.yml)

Tells you, in plain language, whether your deployed app is set up safely, and exactly how to fix what isn't on your host.

> **Only test apps you own or have permission to test.** Against someone else's site, unusual requests can look like an attack and may be illegal.

## Install

Requires Python 3.10 or newer.

```bash
uv tool install deploy-checkup
```

[uv](https://docs.astral.sh/uv/) installs command-line tools in their own environment. To try it once without installing anything, run `uvx deploy-checkup https://your-app.com`. `pipx install deploy-checkup` and `pip install deploy-checkup` work too.

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
| `--active` | Also run the active rate-limit test (needs your permission too) |
| `--rate-limit-path` | The path the rate-limit test sends its burst to (default: the health path) |
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

Each finding says what was found, why it matters, and how to fix it.

| Level | Meaning |
|---|---|
| **PASS** | Checked, and it's set up well. |
| **WARNING** | Probably worth fixing, but your app may be fine without it. Used whenever deploy-checkup can't be sure. |
| **FAIL** | Something is clearly broken or unsafe. Fix this first. |
| **INFO** | Good to know, such as a check that was skipped or a hint that may not apply. |

The command exits with code `1` if anything fails and `0` otherwise.

### Use it in CI

Run it after each deploy, so a broken setup fails the pipeline. In GitHub Actions, use the action:

```yaml
- uses: Nandhagopal2912/deploy-checkup@v0.2.0
  with:
    url: https://your-frontend.onrender.com
    api: https://your-api.onrender.com
    i-own-it: "true"
```

| Input | Meaning |
|---|---|
| `url` | Your frontend's address (required) |
| `api` | Your API's address, if it is separate |
| `health-path` | The API's health check path (default `/health`) |
| `i-own-it` | `"true"` also runs the probing checks. Only for apps you own or have permission to test. |

Anywhere else, install and run the command directly:

```bash
pip install deploy-checkup
deploy-checkup https://your-frontend.onrender.com --api https://your-api.onrender.com --yes-i-own-it
```

`--yes-i-own-it` runs the probing checks without the question nobody can answer in CI. Leave it out to run only the gentle checks.

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
| **rate_limit** | API (or frontend) | Once the rate limit blocks you, does a fake `X-Forwarded-For` get you unblocked? **Active:** runs only with `--active` and your permission. |

The headers check skips the API on purpose: a JSON API doesn't need CSP or X-Frame-Options, and flagging them would be a false alarm.

**Fix hints match your host.** When a response carries Render's `x-render-origin-server` header, fixes point to the exact place in the Render dashboard. On any other host you get general advice.

### Probing checks ask first

Most checks send ordinary requests any browser could send. The exposed files check asks for paths like `/.env`, which on someone else's site can look like an attack. So deploy-checkup asks *"Do you own this site?"* before running it. If nobody can answer (in CI, for example), it is skipped and the report says so, unless you pass `--yes-i-own-it`. A leaked file's contents are never shown in the report.

### The active rate-limit test

Many apps limit how often one visitor can call them, and identify the visitor by the `X-Forwarded-For` header. But visitors can write that header themselves. If the app trusts the first entry, anyone can bypass the limit by sending a different fake IP each time.

With `--active`, deploy-checkup:

1. sends normal requests until the app answers `429 Too Many Requests` (at most 60),
2. sends one request with a fake `X-Forwarded-For: 203.0.113.7` (an address reserved for documentation, never a real visitor),
3. sends one more normal request, to confirm you're still blocked.

If the fake request gets through while you're still blocked, the limit can be bypassed. The test defaults to the health path, because it's cheap to call; never point `--rate-limit-path` at an endpoint that costs money per request. Afterwards, your own IP may stay blocked on that app for up to a minute.

### Polite by design

Every request uses a 60-second timeout (Render's free tier can take about 50 seconds to wake up) and identifies itself as `User-Agent: DeployCheckup/<version>`, so site owners can see what called them. A normal run sends a few dozen ordinary requests; `--active` adds at most 62 more.

### What it doesn't do

deploy-checkup is a quick first look, not a full security audit:

- It doesn't try to break in, and it isn't a replacement for tools like OWASP ZAP. Apart from the opt-in rate-limit test, it only sends ordinary requests.
- CORS is tested on the one API address you give it, health on one path, and the rate limit on one path with one fake header (`X-Forwarded-For`).
- Cold start detection is a guess from a few timings.
- Fix hints are written for Render first; other hosts get general advice.

## JSON output

`--json` prints the same findings for scripts and CI. Only the JSON goes to standard output; the permission question goes to standard error, so you can save the report safely:

```bash
deploy-checkup https://your-frontend.onrender.com --api https://your-api.onrender.com --json > report.json
```

```json
{
  "tool": "deploy-checkup",
  "version": "0.2.0",
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

The project uses [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/Nandhagopal2912/deploy-checkup.git
cd deploy-checkup
uv sync                         # creates .venv with the exact versions in uv.lock
uv run pytest
uv run deploy-checkup --help
```

`uv sync` installs the project in editable mode plus the `dev` dependency group, so code changes take effect without reinstalling. `uv.lock` pins every version for development and CI only; people who install deploy-checkup still get the ranges from `pyproject.toml`. After changing dependencies, run `uv lock` and commit the updated `uv.lock`. `uv build` makes the wheel and source archive.

Tests never touch the network. Each check receives an `httpx.Client`, and tests pass one built on `httpx.MockTransport`, which answers requests with fake responses. CI runs them on Python 3.10 and 3.13.

[`demo/`](https://github.com/Nandhagopal2912/deploy-checkup/tree/main/demo) holds a deliberately broken app with known flaws, used to prove each check catches what it should. The project's plan is in the [roadmap](https://github.com/Nandhagopal2912/deploy-checkup/blob/main/docs/Deploy%20Doctor%20Roadmap.pdf).

## License

[MIT](https://github.com/Nandhagopal2912/deploy-checkup/blob/main/LICENSE)
