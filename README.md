# Todone

A small, local-first task manager for a human-editable Markdown file, with a command-line tool and an Omarchy Shell plugin.

The data source is `~/Documents/todo.md`. Headings are projects, checkbox items are tasks, `@Name` assigns a task to someone, and a `{YYYY-MM-DD HH:MM}` stamp records when it was created. Everything Todone does not understand is preserved byte for byte, so the file stays yours.

```markdown
# Home

- [ ] Buy paint for the hallway @Bernice {2026-09-16 12:37}
- [o] Mount the shelves @Frances {2026-09-15 09:02}
- [x] Call the plumber
```

## Status

Planning. Nothing runs yet.

- [PLAN.md](PLAN.md) is the design: file format, CLI contract, JSON snapshot, plugin layout, keymap, milestones.
- `design/` holds the source of the visual mockup of the bar widget and overlay. `gen.py` writes the artboards from the running shell's theme tokens.

## Shape

```text
~/Documents/todo.md
        ↕
     todone CLI        Python 3, standard library only
        ↕ JSON
Omarchy bar widget + overlay
```

The CLI owns parsing, validation and every mutation. The plugin never touches the Markdown directly.

## License

MIT
