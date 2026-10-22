# Advanced File Organizer — Python + Tkinter

Educational desktop utility. Test on a disposable folder and back up important data before use.

## Features
- GUI with Tkinter
- File scan and extension-based automatic categorization
- Categorization preview before moving
- Duplicate detection using size prefilter + SHA-256 content hashes
- Duplicate copies moved to `_duplicates` recovery folders, never permanently deleted
- Batch rename with preview and `{name}`, `{ext}`, `{index}`, `{date}` tokens
- Persisted undo journal for the last successful operation
- Timestamped logs in `logs/organizer.log`
- Optional recursive scan and collision-aware names
- Unit tests

## Run
Python 3.10+ recommended. No third-party packages. Tkinter is included with most Windows Python installations; Linux may require `python3-tk`.

```bash
python main.py
```

## Tests
```bash
python -m unittest discover -s tests -v
```

## Usage
1. Choose a test folder with Browse.
2. Scan and review the files.
3. Preview categorization, then Categorize.
4. Find duplicates; Move duplicate copies to preserve one copy per group.
5. Enter a rename pattern, preview it, then Rename.
6. Undo last reverses the latest recorded operation if paths are still safe to restore.

## Rename patterns
- `{index:03d}_{name}` -> `001_report.pdf`
- `{date}_{name}` -> `20261013_report.pdf`
- `copy_{index:02d}_{name}.{ext}` -> `copy_01_report.pdf`
- `{name}_backup` -> `report_backup.pdf`

When `{ext}` is present, include the extension in the pattern yourself. Otherwise the original extension is appended automatically.

## Structure
- `main.py`: app entry point
- `gui/app.py`: Tkinter GUI
- `organizer/service.py`: scan, categorize, duplicate detection, rename, undo
- `organizer/state.py`: persistent undo journal
- `organizer/config.py`: categories and paths
- `tests/test_service.py`: core unit tests

## Notes
Undo refuses to overwrite an existing destination or restore a missing file. External file changes can prevent safe undo. Recursive categorization moves scanned files into category folders at the selected root; inspect the preview first. For very large folders, a future version could add worker threads, progress/cancel, SQLite journaling, and configurable categories.
