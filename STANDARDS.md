# Adopted Mad Mallard standards

Source: https://github.com/drakeg/madmallard-repository-standards
Reviewed revision: `5c43391e7a6860cf9691b45758ee9003f9f0222f`.
ADOPTION.md permits selective existing-project adoption, preserving application
architecture, licensing, data, documentation and stricter project requirements.

- Build, deploy locally, test, fix and proceed to the next ready backlog task
  within each authorized session. Sprint boundaries require no routine approval.
- Keep changes reviewable in PRs; respect protections and required reviews.
  Never merge unreviewed work or invent test/deployment results.
- Maintain README, AGENTS, CONTRIBUTING, SPRINTS, BACKLOG, RELEASES and SECURITY.
  Track acceptance criteria, outstanding defects and rollback steps.
- Keep the verified local badge generator: it explicitly labels Vercel as a
  simulation and derives Python versions from the Dockerfile. Dynamic workflow,
  license and activity badges do not hardcode success. No published release exists.
- Use minimal `contents: read` CI permissions. Do not run central scripts or
  reusable workflows from a moving remote branch. Reconcile future versions
  deliberately, without cross-project access or runtime dependencies.
- Preserve independent Compose projects, volumes, credentials and LAN ports.
  No paid services, destructive data operations or outreach are authorized.
- Prioritize SMB pilot value and measured demand. Pricing and delivery times
  remain hypotheses until supported by real customer evidence.

Local checks: `python3 scripts/validate_repository.py` and the application tests.
This is selective standards adoption, not a template replacement or a claim that
the centralized badge generator is running in this project.
