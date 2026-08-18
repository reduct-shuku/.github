# Agent Skills Registry Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Publish a validated, machine-readable registry of all supported `reduct-shuku` skills at the canonical GitHub Pages endpoint.

**Architecture:** The organization `.github` repository owns source configuration, metadata collection, validation, and the committed registry artifact. The `reduct-shuku.github.io` repository runs the same builder and deploys only the generated `/agent-skills.json` file through GitHub Pages.

**Tech Stack:** Python 3.12, PyYAML, `unittest`, Git, GitHub Actions, GitHub Pages.

---

### Task 1: Specify Registry Behavior

**Files:**
- Create: `tests/test_build_agent_skills.py`
- Create: `tests/test_validate_agent_skills.py`

1. Add fixtures for a multi-skill repository and a repository-level skill.
2. Assert stable name sorting and metadata mapping.
3. Assert failures for malformed frontmatter, partial skill directories, name mismatches, and duplicate names.
4. Assert `--check` detects stale generated output without modifying it.
5. Run `python -m unittest discover -s tests -v`; expect failure because implementation modules do not exist yet.

### Task 2: Implement Builder and Validator

**Files:**
- Create: `scripts/build_agent_skills.py`
- Create: `scripts/validate_agent_skills.py`
- Create: `scripts/__init__.py`
- Create: `requirements.txt`

1. Parse `sources.json` and validate its schema and repository entries.
2. Resolve sources from local directories for tests or clone configured public GitHub repositories for production.
3. Discover only immediate skill directories for `skills-directory`; require repository-root metadata for `repository-skill`.
4. Parse YAML frontmatter and JSON manifests, then enforce source, path, name, and duplicate constraints.
5. Render deterministic UTF-8 JSON and implement normal and `--check` output modes.
6. Validate the generated registry as an independent artifact.
7. Run the complete test suite; expect all tests to pass.

### Task 3: Configure the Organization Registry

**Files:**
- Create: `registry/sources.json`
- Generate: `registry/agent-skills.json`
- Modify: `README.md`
- Modify: `profile/README.md`

1. Configure `ai-research-skills` as `skills-directory` and `intuitive-deep-learning` as `repository-skill`.
2. Build against the checked-out local source repositories.
3. Record the canonical endpoint and explain the progressive-disclosure contract.
4. Run builder `--check` and the standalone validator.

### Task 4: Add Continuous Validation

**Files:**
- Create: `.github/workflows/build-agent-skills.yml`

1. Validate committed registry output on pushes and pull requests that affect registry code or configuration.
2. Refresh the artifact on schedule, manual dispatch, or repository dispatch.
3. Commit scheduled changes with the GitHub Actions bot only when the generated artifact changes.

### Task 5: Publish the Canonical Endpoint

**Files in `reduct-shuku.github.io`:**
- Create: `.github/workflows/deploy-agent-skills.yml`
- Create: `agent-skills.json`
- Create: `README.md`

1. Rebuild the registry from the public organization sources during deployment.
2. Validate and upload a minimal Pages artifact.
3. Enable GitHub Pages with GitHub Actions as the build source.
4. Verify an unauthenticated GET returns JSON containing all three required skills.

### Task 6: Publish Repositories

1. Commit `.github` changes with the configured `dengyuhai` Git identity and push `main`.
2. Create the public `reduct-shuku/reduct-shuku.github.io` repository through the authenticated GitHub API.
3. Commit and push the Pages repository, monitor its deployment workflow, and verify the canonical URL.
