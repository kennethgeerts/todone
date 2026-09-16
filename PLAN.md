# Todone

Todone is a small, local-first task manager for a human-editable Markdown file. It consists of a standalone command-line tool and an Omarchy Shell plugin that uses the CLI as its only backend.

The data source is `~/Documents/todo.md`. The file must stay readable and editable with any text editor.

## Goals

- Organize tasks into named projects.
- Represent todo, in-progress, and done tasks as three persistent states.
- Add, edit, delete, and check tasks.
- Show the newest task first, everywhere.
- Reorder projects.
- Assign tasks to people with inline `@mentions` and filter on them.
- Keep Markdown as the source of truth and preserve everything Todone does not understand.
- Offer predictable human-readable output and a stable JSON interface.
- Provide a native Omarchy bar widget and interactive overlay.

## Non-goals for the MVP

- Due dates, recurrence, priorities, or nested subtasks.
- Tags. Projects are the only grouping dimension; a second one was rejected as not worth the extra UI.
- A people directory. Mentions are free-form names; the plugin only keeps a list for completion.
- CalDAV or cloud synchronization.
- A separate database or background daemon.
- Mobile or cross-platform graphical clients.
- Rich Markdown editing inside the Omarchy overlay.

## Architecture

```text
~/Documents/todo.md
        ↕
     todone CLI
        ↕ JSON
Omarchy bar widget + overlay
```

The CLI owns parsing, validation, and every mutation. The QML plugin never rewrites Markdown directly. This keeps the storage rules in one place and makes the CLI useful on its own.

## Markdown format

Top-level headings are projects. Tasks are checkbox list items beneath them:

```markdown
# Work

- [ ] Todo task @Frances {2026-09-16 12:37}
- [o] In-progress task {2026-09-15 09:02}
- [x] Done task
```

Rules:

- A line starting with `# ` is a project heading.
- A line starting with exactly `- [ ] `, `- [o] `, or `- [x] ` at column 0, beneath a heading, is a task. Nothing else is. A checkbox line before the first heading is a preserved line, and `check` warns about it.
- Project order in the file is authoritative. Task order within a project is where `add` inserts and the tie-break for recency, nothing more.
- Every other line is preserved byte-for-byte and never interpreted, moved, or deleted. That covers blank lines, prose, other bullets, indented items, uppercase markers, and any other Markdown.

The real file, as of 2026-09-16, already follows this format: six projects, 30 tasks across all three states, no timestamps yet, and nothing else but blank lines. One `todone stamp` run brings it in line.

### Mentions

A mention is a token inside the task text that assigns the task to a person. Mentions are read, never rewritten, and stay exactly where the user typed them.

- A mention is `@` followed by a letter, then any run of letters, digits, `_`, or `-`.
- It must start at the beginning of the task text or after whitespace, and end at whitespace or end of line.
- Matching is exact, like project names. `@frances` and `@Frances` are two people. `check` warns when two mentions differ only by case.
- A mention may appear anywhere in the text. The plugin highlights it in place rather than moving it to the end.
- A task may mention several people.
- Mentions are part of the task text and therefore part of the task ID. Adding one is an edit like any other.

Not a mention, by that rule:

| Text | Why |
|------|-----|
| `Mail alice@example.com` | Not preceded by whitespace |
| `Meet @ noon` | No letter after the marker |
| `Order @2 spare parts` | Starts with a digit |

Mentions are free-form names. A household might use `@Frances`, `@Bernice`, `@Chris`, and `@Dana`; the CLI accepts any name, so a new one never needs a config change.

### Timestamps

A timestamp records when a task was created, so every view can show the newest first. It is plain text in the task line, `{YYYY-MM-DD HH:MM}` in local time, for example `{2026-09-16 12:37}`.

- The CLI writes it at the end of the line on `add`. A hand-written task may carry one anywhere in the text or none at all.
- It is recognised only in that exact shape. Any other braces are ordinary text.
- It is never displayed. The CLI's human output, the overlay and the `text` field in JSON all strip it. The snapshot carries it as `created`.
- It is excluded from the task ID, so stamping a line does not change the task's identity.
- Ordering, everywhere: unstamped tasks first, then stamped ones from newest to oldest. Ties break on file order, project order first and then position within the project. An unstamped task counts as newest because a task you just typed by hand is the freshest thing in the file.
- The CLI stamps an unstamped task with the current time the next time it writes that line for any other reason, so the file converges without unrequested rewrites. `todone stamp` stamps every unstamped task at once with the same time, keeping their file order as the tie-break; that is the one-off migration for the existing file.
- Editing the text through the CLI keeps the timestamp. Toggling keeps it. Only the user changes it, by editing the file.
- `check` warns about a task with two timestamps and uses the last one.

### Edge cases

Decide these once, in the parser, and cover each with a fixture:

- Duplicate project headings are a `check` warning. Every command that takes a project name also accepts `--project-index N`, counted from 1 in file order. Ambiguous names are refused with exit code 5 and require the index.
- Project names match exactly after trimming trailing whitespace. No case folding.
- Task text is everything after the marker. Trailing whitespace is preserved on unmodified lines and stripped on edited ones.
- A heading with no tasks is a valid empty project.
- A missing file is an error for every command except `project add`, which creates it, and `check`, which reports it.
- `add` inserts the new task as the first task line of the project, directly after the heading and any preserved lines that precede the first task, so the file reads newest-first like the overlay. It appends the timestamp to the line.
- A file without a trailing newline stays that way after a write, and vice versa.

### Task lifecycle

Toggle cycles through all three states:

```text
todo -> in progress -> done -> todo
```

State changes never remove a task. A done task stays in its project until the user deletes it. The CLI's human output hides done tasks unless `--all` is given; the overlay always shows them. Neither archives, moves, or deletes anything.

## Task identity and revisions

IDs are not embedded in the Markdown. Each JSON snapshot carries:

- A task ID: a short hash of the project heading, the task text without its timestamp, and the occurrence index among identical texts in that project. The state marker and the timestamp are excluded, so an ID survives toggling or stamping its own task and the overlay can keep its selection.
- A document revision: a hash of the file bytes.
- The source line of every project and task, for diagnostics only. Line numbers are never an identity.

Mutations accept a task ID and an expected revision. If the file changed after the UI loaded it, the CLI refuses with exit code 3 and the plugin reloads. Because the ID is content-based, the plugin can re-resolve the task in the fresh snapshot and retry without asking, unless the task itself changed.

## CLI

The executable is `todone`. It does not collide with Todoman's former `todo` command.

```text
todone list [--project NAME] [--person NAME] [--all] [--json]
todone people [--json]
todone add --project NAME TEXT
todone stamp [--json]
todone edit TASK_ID TEXT [--revision REV]
todone toggle TASK_ID [--revision REV]
todone state TASK_ID todo|inprogress|done [--revision REV]
todone delete TASK_ID [--revision REV] [--yes]

todone project list [--json]
todone project add NAME
todone project rename NAME NEW_NAME
todone project move NAME up|down|top|bottom
todone project delete NAME [--force] [--yes]

todone check [--json]
```

Behaviour:

- `list` hides done tasks in human output; `--all` shows them. `--json` always contains every task. Both follow the ordering rule under Timestamps.
- `--person` filters `list`. It may repeat, and a task must then mention every given name. The `@` is optional, so `--person Frances` and `--person @Frances` are the same.
- `people` lists every distinct mention with its open-task count, ordered by first appearance.
- `stamp` adds the current time to every task that has none and changes nothing else. It is the only mutation that touches more than one task.
- Mentions are added or removed by editing the text. There is no `assign` command, so the file stays the single vocabulary.
- `delete` and `project delete` prompt for confirmation. `--yes` skips the prompt for scripts and the plugin, which shows its own confirmation.
- `project delete` refuses a project that still has tasks unless `--force` is given. It also writes a timestamped backup next to the file.
- `project rename` refuses a name that already exists.
- `--project-index N` replaces `--project NAME` or a positional project name on any command, for ambiguous headings.
- Every mutation accepts `--json` and prints the fresh snapshot after the write, so the plugin never needs a second `list` call.

Conventions:

- Default file `~/Documents/todo.md`, overridden by `--file PATH` or `TODONE_FILE`. The flag wins.
- Human-readable output on stdout, machine-readable with `--json`.
- Errors and diagnostics on stderr with a non-zero exit code.

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unexpected failure |
| 2 | Usage error |
| 3 | Stale revision, mutation refused |
| 4 | File missing, unreadable, or failed validation |
| 5 | Task or project not found, or project name ambiguous |
| 6 | Confirmation declined |

### JSON snapshot

```json
{
  "schemaVersion": 1,
  "file": "/home/frances/Documents/todo.md",
  "revision": "9f2c...",
  "projects": [
    {
      "id": "a1b2",
      "name": "Work",
      "line": 1,
      "tasks": [
        { "id": "c3d4", "text": "Todo task @Frances", "state": "todo", "line": 3,
          "created": "2026-09-16 12:37", "people": ["Frances"] }
      ]
    }
  ],
  "people": [ { "name": "Frances", "open": 1 } ],
  "warnings": [
    { "line": 27, "kind": "duplicate-project", "message": "Project 'Work' appears twice" },
    { "line": 31, "kind": "mention-case", "message": "Mentions '@Frances' and '@frances' differ only by case" }
  ]
}
```

`text` is the task text with the timestamp removed and surrounding whitespace trimmed; mentions stay in it. `created` is the timestamp as written, or `null` when the task has none. Tasks within each project are already in recency order; the overlay merges projects by the same rule. `people` on a task holds the bare names in text order without duplicates. The top-level `people` array aggregates the whole file so the overlay builds its filter row from one snapshot. `warnings` carries the same findings as `todone check`. Error responses under `--json` use `{"error": {"code": 3, "message": "..."}}`.

## File safety

Every mutation:

1. Acquires an advisory `fcntl.flock` on a sidecar file, `todo.md.lock`, next to the document. Locking the document itself does not work because step 6 replaces its inode.
2. Reads and validates the current file.
3. Verifies the expected revision when supplied.
4. Changes only the relevant lines.
5. Writes a temporary file in the same directory.
6. Flushes and fsyncs it, then replaces the original with `os.replace`.
7. Preserves the original mode bits and final-newline convention.

Routine operations rely on atomic writes alone. Automatic backups can be added later if real-world use warrants them.

## Implementation

Python 3 with the standard library only. Omarchy ships Python 3.14, so nothing needs installing, and the standard library covers JSON, locking, hashing, and atomic writes.

The parser and mutation logic live in `document.py` and `model.py`, independent of the argument parser in `cli.py`, so they can be unit tested directly. The package also runs as `python3 -m todone`, which gives the plugin a fallback that does not depend on `PATH`. A packaged executable or a later rewrite remains possible without changing the CLI contract.

## Omarchy plugin

Plugin ID `frances.todone` for now; switch to a reverse-domain ID before publishing. The `omarchy.*` namespace is reserved.

The plugin lives under `plugin/` in the repository and is installed by copying into `~/.config/omarchy/plugins/frances.todone/`. The validator refuses symlinks inside a plugin folder, so the install script must copy. The shell hot-reloads plugin code on save. Never modify `/usr/share/omarchy/`.

### Manifest

As enforced by `omarchy plugin validate` and `shell/services/PluginRegistry.qml`:

```json
{
  "schemaVersion": 1,
  "id": "frances.todone",
  "name": "Todone",
  "version": "0.1.0",
  "author": "Kenneth",
  "license": "MIT",
  "description": "Markdown todo list in the Omarchy bar with a keyboard-driven overlay.",
  "kinds": ["bar-widget", "overlay"],
  "keepLoaded": true,
  "entryPoints": {
    "barWidget": "BarWidget.qml",
    "overlay": "TodoOverlay.qml"
  },
  "barWidget": {
    "displayName": "Todone",
    "description": "Open task count. Click to open the overlay.",
    "category": "Productivity",
    "allowMultiple": false,
    "defaultSection": "right",
    "defaults": {
      "todoFile": "~/Documents/todo.md",
      "cliPath": "todone",
      "countInProgress": true,
      "people": ""
    },
    "schema": [
      { "key": "todoFile", "type": "path", "label": "Todo file", "defaultValue": "~/Documents/todo.md" },
      { "key": "cliPath", "type": "string", "label": "todone executable", "defaultValue": "todone",
        "description": "Command or absolute path. The shell's PATH may not include ~/.local/bin." },
      { "key": "countInProgress", "type": "boolean", "label": "Count in-progress tasks in the bar", "defaultValue": true },
      { "key": "people", "type": "string", "label": "People offered for @ completion", "defaultValue": "",
        "description": "Comma-separated. Names found in the file are offered anyway." }
    ]
  }
}
```

`schemaVersion` must be the JSON number 1, and each declared kind needs its matching entry point. Settings are declared on the `barWidget` block because that is the only settings surface the shell offers. `keepLoaded: true` keeps the overlay mounted between summons, like the first-party clipboard and reminders overlays.

Validate with `omarchy plugin validate plugin`. Enable with `omarchy plugin enable frances.todone right`. If a code change fails to apply, run `omarchy-shell shell rescanPlugins`.

### Bar widget

```text
 …  ✓ 7  │  12:37 
```

- A task icon and the count of todo tasks, plus in-progress tasks when `countInProgress` is on.
- Click runs `omarchy-shell shell toggle frances.todone '{}'` through `root.bar.run`, the same path the first-party menu widget uses.
- Theme colours and metrics from the shared `Color` and `Style` singletons in `qs.Commons`.
- A warning glyph instead of a count when the CLI fails or the file does not parse.

### Overlay

A visual mockup drawn with the shell's own theme tokens lives at <https://claude.ai/code/artifact/92c92174-77e7-4ce2-948c-d79224d9edc8>; its source is `design/`. The sketches below carry the same layout. Project and people names are placeholders.

```text
┌──────────────────────────────────────────────────────────────────┐
│  Search tasks…                                                   │
│  #Work   #Home   #Garden   #Admin   #Car   #Holiday              │
│  @Frances   @Bernice   @Chris   @Dana                            │
├──────────────────────────────────────────────────────────────────┤
│  ▸ ○  Todo task ⟨@Frances⟩                                       │
│    ○  Buy paint for the hallway ⟨@Bernice⟩ ⟨@Dana⟩               │
│    ◐  Fix the fence ⟨@Chris⟩                                     │
│    ◐  In-progress task                                           │
│    ○  Call the plumber                                           │
│    ○  Order seeds                                                │
│    ●  Done task                                                  │
├──────────────────────────────────────────────────────────────────┤
│  +  Add to #Work… (# project, @ people)                          │
└──────────────────────────────────────────────────────────────────┘
```

Each bullet carries its project's colour. The same overlay with `#Home` and `@Frances` selected, with the quick-add going to `Home` and `@Frances` pre-filled:

```text
│  Search tasks…                                                   │
│  #Work  [#Home]  #Garden   #Admin   #Car   #Holiday              │
│ [@Frances]  @Bernice   @Chris   @Dana                            │
├──────────────────────────────────────────────────────────────────┤
│  ▸ ○  Paint the hallway ⟨@Frances⟩ ⟨@Bernice⟩                    │
│    ◐  Mount the shelves ⟨@Frances⟩                                │
├──────────────────────────────────────────────────────────────────┤
│  +  @Frances Add to #Home…                                       │
```

Layout:

- A search field at the top, in the same place and style as the clipboard overlay's filter line. It matches task text and mentions, case-insensitively, and narrows the list live. Empty by default.
- Two button rows below it. The first has one button per project in file order, labelled `#Name` to echo the Markdown heading. The second has one button per name from the snapshot's `people` array in file order, labelled `@Name`. Nothing is selected by default, so the overlay opens on every task.
- At most one selection per row. Clicking a selected button clears that row. A task shows when it passes the search and both rows. No button is special: `@Frances` is a person like any other.
- Selections and the search persist while the overlay stays loaded and reset when the shell restarts. A selected project or person that disappears from the file clears that row.
- The task list is one flat list, newest first, whatever the filters. It is never split into project groups.
- Each project has a colour, taken from the theme palette in file order (blue, green, yellow, magenta, orange, cyan, then cycling), so it follows the theme. The colour is used on the project's filter button, on the state bullet of every task in that project, and on the project name in the quick-add placeholder. People have no colour.
- Done tasks are always shown, in their recency position, with a filled bullet and dimmed text. There is no done filter. Deleting is the only way to make a task disappear.
- A quick-add field sits at the bottom, just a `+` and a text field. The task's project comes from the text: the first `#Project` token that matches an existing project decides where the task goes and is stripped before the line is written. With no such token, the task goes to the selected project filter, or to the first project when none is selected. The placeholder names that default, "Add to #Work…", with the project in its colour, and follows the filter. A `#word` matching no project stays as plain text.
- When a person is selected, the field opens pre-filled with that mention, which the user can delete.
- Mentions render as neutral chips in place within the task text, using the `⟨@Name⟩` positions above.
- Typing `@` in the quick-add or edit field opens a completion popup with the configured people merged with names found in the file. Typing `#` in the quick-add field opens the same popup with the projects. Enter accepts, Escape dismisses, and the text is otherwise free.
- `Color.menu.*` surface tokens, so themes that style the menu style the overlay.

Actions on the task under the cursor: cycle state, edit in place, and delete with an inline confirmation on the task's own row. A task's project is set at creation and changed by editing the file. Clear empty, parse-error, and concurrent-edit states replace the list rather than overlaying it.

Keymap. The overlay opens with the cursor on the first task and no text field focused. Two keys enter a text field, and `Esc` leaves it. The filter buttons are mouse-only.

| Key | Action |
|-----|--------|
| `↓` / `↑` | Move the cursor through the list |
| `Space` | Cycle the state of the task under the cursor |
| `Enter` | Edit the task under the cursor in place; `Enter` saves, `Esc` cancels |
| `Backspace` | Delete the task under the cursor; `Enter` confirms, `Esc` cancels |
| `/` | Focus the search line; typing filters live, `Enter` or `Esc` returns to the list, and `Esc` on an empty line clears the filter |
| `a` | Focus the quick-add field; `Enter` adds, `Esc` returns to the list |
| `Esc` | In the list: close the overlay |

Keys act on the list only while no text field has focus.

### Data flow

`Model.js` owns the snapshot and a single command queue shared by the bar widget and the overlay:

- Load runs `todone list --json` through a Quickshell `Process` and stores the snapshot and its revision.
- Each mutation runs one CLI command with `--revision` and `--json` and replaces the snapshot with the output. Commands are serialized, so a second action waits rather than racing.
- Exit code 3 triggers a reload. If the same task ID exists in the new snapshot, the action is retried once. Otherwise the overlay asks the user to retry.
- A watch on the todo file's directory, debounced by about 200 ms, triggers a reload so manual edits appear without restarting the shell. The directory is watched rather than the file because atomic replacement changes the file's inode.

## Repository layout

```text
todone/
├── PLAN.md
├── README.md
├── pyproject.toml
├── install.sh
├── src/todone/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── document.py
│   └── model.py
├── tests/
│   ├── fixtures/
│   ├── test_cli.py
│   └── test_document.py
├── plugin/
│   ├── manifest.json
│   ├── BarWidget.qml
│   ├── TodoOverlay.qml
│   └── Model.js
└── design/
    ├── gen.py
    ├── canvas.json
    └── *.dc.html
```

`design/` holds the mockup source. `gen.py` writes the artboards from the shell's tokens; the published canvas is rebuilt from them.

## Milestones

### 1. Read-only CLI

- Define the document model and the JSON snapshot above.
- Parse projects, tasks, mentions, and timestamps, including the edge cases listed.
- Implement `list` with `--person`, `people`, `project list`, and `check` with its warnings: duplicate project, orphan checkbox line, mention case, double timestamp.
- Add fixtures that mirror the shape of the real file with placeholder text, so private task text never enters the repository. Include one fixture with mentions and timestamps, one with every non-mention case from the table, and one with no timestamps at all.
- Verify that parse then serialize reproduces every fixture byte-for-byte.

### 2. Safe mutations

- Add, edit, toggle, and set task state.
- Stamp on `add`, stamp unstamped lines on their next write, implement `stamp`, and sort `list` newest-first.
- Reorder projects.
- Delete tasks and projects with confirmation and `--yes`.
- Implement revision checking, sidecar locking, and atomic writes.
- Return the fresh snapshot from every mutation under `--json`.
- Test every mutation against a fixture and assert that only the expected lines changed.

### 3. Plugin skeleton

- Add and validate the manifest.
- Build the bar widget and overlay shell, load the snapshot, and display every task newest-first with the search line and the two filter rows present but inert.
- Add directory watching and error presentation.
- Confirm how the overlay receives the bar widget's settings and locates the CLI.

### 4. Interactive plugin

- Wire state changes, quick add, edit, and delete through the command queue.
- Wire the search field and the filter rows, and render mention chips.
- Add `@` and `#` completion in the text fields and the keymap above.
- Handle stale revisions by retrying on a matching task ID and asking otherwise.
- Test keyboard and mouse interaction.

### 5. Packaging and daily use

- Add `install.sh`: install the CLI with `uv tool install` or `pipx`, copy the plugin, and enable it.
- Add shell completions if they materially improve use.
- Use Todone against a copy of the real file before switching the default.
- Document recovery: the lock sidecar and project-delete backups.

## Risks

- **The shell's PATH.** `omarchy-shell` may not see `~/.local/bin`, so a `todone` installed by `uv tool` or `pipx` can be invisible to the plugin. The `cliPath` setting and the `python3 -m todone` fallback cover this.
- **Editors with a stale buffer.** An editor that saves an old buffer overwrites Todone's changes. The revision check protects Todone's side only. Document this.
- **Settings for overlays.** No first-party overlay declares settings. If the overlay cannot read the `barWidget` settings, fall back to the CLI's own defaults and `TODONE_FILE`.
- **Task ID collisions.** Short hashes are not unique by construction. Use at least 8 hex characters and let the occurrence index disambiguate identical texts.
- **Mentions change the ID.** Because mentions live in the text, adding one through the overlay changes the task ID and can drop the selection. The overlay re-selects by the fresh snapshot's line number immediately after its own edit, which is safe because it just wrote that line.
- **Accidental mentions.** Prose such as `@ noon` is excluded by the grammar, but a typo in a name creates a new person. Completion and the `check` case warning reduce this; they do not eliminate it.
- **Timestamps clutter the file.** Every CLI-written task line ends in `{2026-09-16 12:37}`. That is the price of keeping recency in the Markdown itself rather than in a second file, and it is accepted. Hand-written tasks need no stamp.
- **Button rows overflow.** Many projects or people push the rows past the overlay width. Wrap the rows before shrinking the buttons; hiding buttons would hide data.

## MVP acceptance criteria

- The Markdown remains understandable and manually editable.
- Parsing and listing never alter the file.
- Every fixture survives parse and serialize byte-for-byte.
- All mutations are atomic and covered by tests.
- Projects can be reordered without unrelated formatting changes.
- `add` puts a task at the top of its project and the overlay shows it first.
- Timestamps are never displayed and never change a task's ID.
- Marking a task done never removes, archives, or relocates it. Only the explicit delete action removes a task.
- Mentions are recognised exactly per the grammar, every non-mention case in the table stays plain text, and `list --person` filters correctly.
- Adding a mention changes only that task's line.
- Manual edits appear in the overlay automatically.
- Concurrent edits never change the wrong task.
- The plugin passes `omarchy plugin validate`.
- The bar widget and overlay work after `omarchy restart shell`.
