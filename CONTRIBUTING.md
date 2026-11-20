# Contributing
Open an issue describing the problem, acceptance criteria, risk and tests before feature changes. Maintainers triage into the current Sprint or backlog; urgent break/fix may bypass sprint planning. Branch from main; use a scoped PR with tests, documentation, linked issue and any migration notes. PR review and passing CI are required before merge. Never include secrets, customer data or credentials. Keep each installation independent of other products. Local validation: `python3 -m unittest discover -s tests -v` and `docker compose config`.


README badge maintenance is part of each relevant PR. Contributors must preserve the badge standards in `AGENTS.md` and run `python3 scripts/validate_badges.py` after changing tool versions, workflows, releases, deployment configuration or licenses.
