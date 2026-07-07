# Submitting EDIBlime to Package Control

Maintainer checklist for publishing this package on
[packagecontrol.io](https://packagecontrol.io). This file is `export-ignore`d
in `.gitattributes`, so it never ships to users.

## Already done (in this repo)

- [x] Package name **EDIBlime** passes the naming rules: no "Sublime" in the
  name, no periods, no restricted characters, ASCII-only, CamelCase.
- [x] One package per repository, package root = repository root.
- [x] `LICENSE` (MIT) and `README.md` at the root; copyright holder updated
  to "EDIBlime contributors".
- [x] `messages.json` + `messages/` install and update messages are valid and
  every referenced file exists.
- [x] No `.pyc`, `__pycache__` or `package-metadata.json` tracked;
  `.gitignore` guards all of them.
- [x] All tracked filenames are ASCII and Windows-safe.
- [x] `.gitattributes` keeps development-only files (`tests/`, this file,
  git metadata) out of the release zipball. Runtime files — `.python-version`
  (selects the Python 3.8 plugin host), `messages/`, `samples/` — do ship.
- [x] Works as a zipped `.sublime-package`: all resource access goes through
  the `sublime` API, so no `.no-sublime-package` marker is needed.
- [x] Key bindings are context-scoped to the package's own syntaxes and never
  shadow other packages in ordinary files.
- [x] Minimum Sublime Text build verified from actual API usage: **4095**
  (`sublime.KIND_ID_COLOR_*`, used at module import). Any stable ST4 release
  (4107+) qualifies.

## Remaining steps (in order)

### 1. Merge and set the default branch

Merge the submission branch into `main`, and set `main` as the repository's
**default branch** on GitHub (Settings → General → Default branch — it
currently points at `claude/EdiBlime-main`). Reviewers and users land on the
default branch's README.

### 2. Tag the release

Package Control resolves releases **exclusively from semver git tags**
(`"tags": true`). No tag exists yet — without one the submission is rejected
with "no releases found". On the release commit on `main`:

```sh
git tag 0.2.0
git push origin 0.2.0
```

Use a bare semver tag (no `v` prefix) so it matches the `messages.json` keys.
Every future release is a new, higher tag; commits after a tag do not ship
until the next tag.

### 3. Add the package to the channel

1. Fork <https://github.com/wbond/package_control_channel> and clone the fork.
2. Edit `repository/e.json` and insert the entry below into the `"packages"`
   array in **case-insensitive alphabetical order** (`EDIBlime` sorts between
   `EasyClangComplete`-style "Ea…" names and "EJ…" names). The file uses
   tabs for indentation.

   ```json
   {
   	"name": "EDIBlime",
   	"details": "https://github.com/encefalopiatto/EDIBlime",
   	"labels": ["edi", "edifact", "x12", "hl7", "tradacoms", "formatting", "language syntax", "converter", "validation"],
   	"releases": [
   		{
   			"sublime_text": ">=4095",
   			"tags": true
   		}
   	]
   }
   ```

3. Validate: install the **ChannelRepositoryTools** package in Sublime Text,
   open the channel repo folder, and run
   **ChannelRepositoryTools: Test Default Channel** from the Command Palette.
4. Commit, push to the fork, and open a pull request titled **"Add EDIBlime"**.
   Mention in the description: what the package does (beautify / minify /
   annotate / validate EDI — EDIFACT, X12, TRADACOMS, HL7), and that a search
   for existing EDI packages was done to rule out duplicates.

### 4. After the PR is merged

- The package appears on packagecontrol.io within the hour; install it via
  **Package Control: Install Package** to smoke-test.
- To release updates: bump the version, add a `messages/<version>.txt` entry
  in `messages.json`, tag, and push the tag — no new channel PR needed.
