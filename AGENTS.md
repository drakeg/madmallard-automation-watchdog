# Agent contributor rules
Operate only inside this repository. Never inspect or modify unrelated repositories, services, databases, containers or customer workloads. Maintain SPRINTS.md and BACKLOG.md for scope changes. Add an issue for new features, and attach each PR to an active-sprint issue or backlog item (break/fix exempt). Validate tests and docs before opening PRs. Prefer standard-library or license-audited open source. Do not store secrets in Git, contact prospects, provision cloud resources, or pay for APIs. Never merge unreviewed changes. Leave running containers and persistent volumes intact unless owned by this project. Include PR URL and test evidence in progress updates.

## README badges

Keep the generated badge block immediately below the root README title, in three
compact rows: stack, deployment support, and dynamic CI/license/activity plus
contribution links. Use `python3 scripts/readme_badges.py` after changing stack,
versions, workflows, licensing or deployment configuration; CI runs `--check`.
Use verified configuration versions, official workflow badges and Shields.io.
Never hardcode build success/security results or imply that configuration proves
a healthy deployment. Vercel is explicitly a simulation. No AWS/ECS/EKS badge is
supported yet. Add a dynamic latest-release badge when a first release is actually
published; none existed at adoption. Preserve all other README content and useful
badges, removing unsupported or duplicate claims.

Central source of truth: https://github.com/drakeg/madmallard-repository-standards.
At adoption it contained only a placeholder README, without usable templates or
a generator. This local implementation follows the user's requirements; reconcile
it with the published central standards when available. Do not invent central rules
or make this repo's CI depend on a moving remote branch.
