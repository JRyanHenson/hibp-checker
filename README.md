# hibp-webapp

A cybersecurity micro-app that checks email addresses against the [Have I Been Pwned](https://haveibeenpwned.com) API. Deployed as part of the [ryanhenson.io](https://ryanhenson.io/tools/hibp/) platform.

Live at: **[ryanhenson.io/tools/hibp/](https://ryanhenson.io/tools/hibp/)**

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask |
| Server | Gunicorn |
| Container | Docker (multi-stage, non-root) |
| Hosting | AWS ECS Fargate |
| Registry | Amazon ECR |
| Secrets | AWS Secrets Manager |
| CI/CD | GitHub Actions |

## How It Works

The app accepts an email address via a form POST and queries the HIBP v3 API. Results are rendered server-side and returned as a styled HTML response matching the terminal theme of the main site.

All routing is prefixed under `/tools/hibp/` so the ALB on the main platform can route traffic to this service using path-based rules.

## Local Development

**Requirements:** Python 3.12, a [HIBP API key](https://haveibeenpwned.com/API/Key)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

HIBP_API_KEY=your_key_here flask --app app run -p 8000
```

Open [http://localhost:8000/tools/hibp/](http://localhost:8000/tools/hibp/).

## Running Tests

```bash
pytest -v
```

## Docker

```bash
# Build
docker build -t hibp-webapp:local .

# Run
docker run -p 8000:8000 -e HIBP_API_KEY=your_key_here hibp-webapp:local
```

## CI/CD Pipeline

The pipeline runs on every push to `main` and weekly for security patch rebuilds.

**Security gates (run in parallel, all must pass before deploy):**

| Gate | Tool | Protects Against |
|---|---|---|
| SAST | Bandit | Insecure Python patterns, injection flaws |
| Secrets | Gitleaks | Credentials committed to git history |
| Dependencies | pip-audit | Known CVEs in Python packages |
| Container | Trivy | OS and package CVEs in Docker image |

**Deploy steps (only on gate pass, only on push to main):**
1. Build Docker image with `--pull` for latest base image
2. Trivy container scan — fails on CRITICAL or HIGH
3. Push to ECR (tagged with commit SHA and `latest`)
4. Force new ECS deployment

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `HIBP_API_KEY` | Yes | Have I Been Pwned API key — injected at runtime from AWS Secrets Manager |
| `HIBP_USER_AGENT` | No | User-agent string sent to HIBP API (default: `ryanhenson-hibp`) |

In production, `HIBP_API_KEY` is stored in AWS Secrets Manager at `hibp/HIBP_API_KEY` and injected by the ECS agent at container startup. It is never stored in the task definition or passed as a plaintext environment variable.

## Security Controls

- Container runs as non-root user (`appuser`, uid 1001)
- Multi-stage Docker build — pip and build tools do not exist in the final image
- `.dockerignore` excludes test files, virtual environment, and git history from the build context
- API key fetched from AWS Secrets Manager at runtime — never in source code or task definitions
- Gunicorn configured with worker timeout to prevent hanging processes
