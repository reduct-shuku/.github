# Agent Skills Registry

The public discovery endpoint is:

```text
https://reduct-shuku.github.io/.well-known/agent-skills.json
```

`agent-skills.json` is generated. Do not edit it by hand. Skill names and descriptions come from each `SKILL.md` frontmatter; versions and source locations come from each `shuku.json`.

To add a repository, update `sources.json`, then build and validate the artifact:

```bash
python -m pip install -r requirements.txt
python scripts/build_agent_skills.py
python scripts/build_agent_skills.py --check
python scripts/validate_agent_skills.py
```

For unpublished local source changes, pass the directory containing the checked-out repositories:

```bash
python scripts/build_agent_skills.py --source-root ..
```
