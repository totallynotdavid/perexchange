# Releasing

The `perexchange` package is published to PyPI from a version tag. The release
command prepares the release and pushes the tag. The tag starts the release
workflow.

## Write the release notes

Write [`.github/release-notes.md`](../.github/release-notes.md) for the new
version, commit it to `master` and push it. The first line must be exactly
`perexchange 2.1.0 is out.` with the new version. The rest is the announcement:
what changed, what broke and how to upgrade. The workflow puts the file at the
top of the GitHub release and appends GitHub's list of changes below it.

## Release a version

Run the command from a clean `master` that equals `origin/master`:

```bash
mise run release 2.1.0
```

The version must be greater than the current one, and the first line of the
release notes must announce it. The tag `v2.1.0` must not exist locally or on
`origin`. The command:

1. Sets `version` in `packages/core/pyproject.toml`.
2. Runs `uv lock` and checks that both files hold the new version.
3. Runs `mise run check`.
4. Commits both files as `build: release perexchange 2.1.0`.
5. Creates the annotated tag `v2.1.0`.
6. Pushes the commit and the tag together with `git push --atomic`.

If a step fails, the command restores the version, lock file, commit, and tag,
and pushes nothing. Fix the cause and run it again.

To check the preconditions without changing anything, add `--dry-run`:

```bash
mise run release 2.1.0 --dry-run
```

## What the workflow does

Pushing a tag that matches `v*.*.*` starts
[`.github/workflows/publish.yml`](../.github/workflows/publish.yml), which:

1. Runs `mise run check`, and the core unit tests on Python 3.12.
2. Builds one wheel and one source distribution, and checks both.
3. Installs the wheel and checks that its version matches the tag.
4. Publishes both to PyPI.
5. Creates the GitHub release with both files attached and the release notes as
   its body, followed by GitHub's list of changes.

If a step fails, later steps do not run. GitHub creates the release only after
PyPI accepts the files.

The workflow rejects a tag that does not point to a commit reachable from
`master`, whose version differs from `version` in
[`packages/core/pyproject.toml`](../packages/core/pyproject.toml), or whose
version is not the one in the first line of the release notes.

## Dry run

The same workflow runs on every pull request and on a manual run
(`gh workflow run publish.yml --ref <branch>`). It builds, checks and installs
the release as on a tag. It skips the PyPI upload and the GitHub release. With
no tag, it holds the first line of the release notes to the version in
`packages/core/pyproject.toml`.

A `preflight` job runs on every event. It reads each `environment:` that
`publish.yml` names and fails when the repository has no environment of that
name. A tag release does not publish until it passes.

## PyPI publishing

The publish job uses the repository's PyPI trusted publisher and the `pypi`
GitHub environment. It authenticates with a short-lived OIDC token, so no PyPI
token is stored in the repository.

To set it up in a fork:

1. In the repository, open Settings, Environments, and create `pypi`. Add
   required reviewers if you want to approve each release.
2. On pypi.org, open the project, Manage, Publishing, and add a GitHub trusted
   publisher with these values:
   - Owner: the account that owns the repository.
   - Repository name: `perexchange`.
   - Workflow name: `publish.yml`.
   - Environment name: `pypi`.

The environment name in step 2 must equal the one in step 1 and the `name:` of
the `pypi` job in `publish.yml`. PyPI cannot be queried from CI, so the
preflight job checks only the repository side.
