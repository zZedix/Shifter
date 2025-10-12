# Release Checklist

Publishing Shifter to PyPI should follow a predictable, repeatable process. Use this checklist for each release.

## 1. Prepare the Codebase
- [ ] Update `pyproject.toml` with the new semantic version.
- [ ] Update any release notes or changelog entry (if maintained separately).
- [ ] Confirm dependency pins are current and still satisfy supported environments.

## 2. Validate Packaging
- [ ] Run `python -m pip install --upgrade build twine`.
- [ ] Build distributables: `python -m build`.
- [ ] Inspect the generated archives under `dist/` (ensure templates and web assets are included).
- [ ] Run `twine check dist/*` to validate metadata.

## 3. Smoke Test the Wheels
- [ ] Create a temporary virtual environment.
- [ ] Install the freshly built wheel: `python -m pip install dist/shifter-<version>-py3-none-any.whl`.
- [ ] Execute `shifter --help` and `python -m shifter status` (mocked if run on a non-Linux host).
- [ ] Verify that the web UI launches: `python -m shifter serve --help`.

## 4. Publish
- [ ] Upload packages with `twine upload dist/*`.
- [ ] Confirm the new version appears on [PyPI](https://pypi.org/project/shifter/).
- [ ] Tag the release in version control (`git tag vX.Y.Z && git push origin vX.Y.Z`).

## 5. Post-Release
- [ ] Update documentation links if necessary.
- [ ] Announce the release in the appropriate communication channels.
- [ ] Create follow-up issues for deferred enhancements or known limitations.

Maintaining this checklist keeps releases predictable and helps catch packaging regressions before they reach production.
