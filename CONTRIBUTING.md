# Contributing
Open an issue describing the problem, acceptance criteria, risk and tests before feature changes. Maintainers triage into the current Sprint or backlog; urgent break/fix may bypass sprint planning. Branch from main; use a scoped PR with tests, documentation, linked issue and any migration notes. PR review and passing CI are required before merge. Never include secrets, customer data or credentials. Keep each installation independent of other products. Local validation: `python3 -m unittest discover -s tests -v` and `docker compose config`.

README badges follow the convention in AGENTS.md. Regenerate with
`python3 scripts/readme_badges.py`, then validate with
`python3 scripts/readme_badges.py --check`. The script derives support and versions
from repository files and uses dynamic endpoints for workflow/license/activity.
It does not claim that deployments are running or perform network status checks.
Revisit release badges when publishing the first release under RELEASES.md.
