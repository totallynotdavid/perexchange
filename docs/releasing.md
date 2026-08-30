# Releasing

The core package is published from a version tag. The workflow runs the checks for that
tag, builds one wheel and one source distribution, checks both artifacts, publishes them
to PyPI, and then creates the GitHub release.

The release workflow does not change files, create commits, or push tags. Do those steps
locally so the version change and release commit can be reviewed.

## Prepare a release

1. Update `version` in [`packages/core/pyproject.toml`](../packages/core/pyproject.toml).
2. Regenerate and check the lock file:

   ```bash
   uv lock
   ```

3. Run the full local checks:

   ```bash
   mise run check
   ```

4. Commit the version and lock-file changes. Set `VERSION` to the version you prepared:

   ```bash
   VERSION=2.0.0
   git add packages/core/pyproject.toml uv.lock
   git commit -m "build: prepare perexchange ${VERSION}"
   git push origin master
   ```

5. Create and push an annotated tag after the commit is on `master`:

   ```bash
   git tag -a "v${VERSION}" -m "Release perexchange ${VERSION}"
   git push origin "v${VERSION}"
   ```

The tag must point to a commit reachable from `master`. The workflow rejects tags that do
not meet that rule or whose version does not match the package metadata.

## PyPI publishing

PyPI publishing uses the repository's trusted publisher and the `pypy` GitHub environment.
The workflow receives a short-lived OIDC token; no PyPI token is stored in the repository.

If a build or check fails, PyPI is not contacted. The GitHub release is created only after
PyPI accepts the artifacts.
