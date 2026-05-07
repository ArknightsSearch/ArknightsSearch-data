# AGENTS.md — ArknightsSearch-data

## What this repo does

Parses Arknights game data tables (JSON) into search-ready data files. Output goes to `data/` and `hash/` (both gitignored).

## Prerequisites & setup

- **Python 3.14** (`.python-version`)
- Dependencies: `aiohttp` (see `pyproject.toml` for met, not `requirements.txt` which is stale)
  - Install: `pip install -e .` or `uv sync`

## Must-run order

```
python fetch_gamedata.py    # clone/pull upstream game data repos → ./gamedata/
python start.py              # parse gamedata/ → ./data/ + ./hash/
```

`start.py` **requires** `gamedata/` to exist first. Never run `start.py` without running `fetch_gamedata.py` first.

## Architecture (what's non-obvious)

### Entry point is a side-effect import

`start.py` contains a single line:

```python
import core.parse.story.save
```

This import triggers the **entire pipeline**. `core/parse/story/save.py` imports all parser modules, which execute at import time. The `save.py` module itself orchestrates sorting and writing output files. There is no `main()` — the import **is** the execution.

### Two-phase data loading

1. **`core/name/`** — loads game JSON tables at import time to build in-memory name→ID mappings (`story_name`, `story_code`, `zone_name`, `char_name`, `activity_id2code`, `month_squad_name`). These populate module-level globals.

2. **`core/parse/story/`** — uses those mappings + text files from `gamedata/` to produce final output.

### Data flow

```
gamedata/excel/*.json  ──→  core/name/*.py  (name mappings)
gamedata/story/*.txt   ──→  core/parse/story/data.py  (text extraction)
                                  ↓
                      core/parse/story/save.py  (sort + write)
                                  ↓
                      data/story/*.json + hash/story/*.txt
```

### StoryData hierarchy

`core/data/story.py` defines the parser:
- `StoryParser.parse(id)` → dispatches to `MemoryData` / `MainData` / `RogueData` / `ActivityStory`
- Stories that can't/shouldn't be parsed raise `InvalidData` (silently filtered)
- See `note/story_structure.md` for the exhaustive list of what's excluded and why

### InvalidData is expected

The `InvalidData` exception in `core/data/error.py` is **not** a bug. It signals stories that should be deliberately skipped (tutorials, guides, certain roguelike content, etc.). Don't "fix" these.

## Conventions & gotchas

### No tests, no CI, no lint config

This is a data-processing script repo. There are no tests, no CI workflows, no linter/formatter config. Don't add infrastructure unless asked.

### Language support is zh_CN only for text indexing

While `support_language = ['zh_CN', 'ja_JP', 'en_US']` in constants, text indexing (`core/parse/story/data.py` line 43) hardcodes `["zh_CN"]`. Metadata (names, zones) is multi-language.

### Path patterns use `%s` string formatting

All paths in `core/constant.py` use `%s` placeholders for language codes:
```python
story_path = os.path.join(resource_path, 'story')  # → gamedata/%s/gamedata/story
```
Callers format with: `story_path % 'zh_CN'`

### story_table IDs can be case-mismatched

Story IDs in `story_table.json` may have different casing than actual file paths on disk. `StoryParser.parse()` calls `.lower()` on the ID before dispatching. When reading text files, it uses the **original** (non-lowered) ID from `story_table`.

### `char_seq.py` blocks on import

Uses `asyncio.run(get_data())` at module level — fetches data from GitHub on every run. If the network request fails, the entire pipeline crashes. This is intentional for freshness.

### `pyproject.toml` vs `requirements.txt` conflict

`requirements.txt` has `aiohttp==3.11.11`. `pyproject.toml` has `aiohttp>=3.13.5`. The `pyproject.toml` is the authoritative source.

### Roguelike data has two chat formats

`core/parse/story/data.py` lines 27-28 handle both `clientChatItemData` (new) and `chatItemList` (old) — don't remove either.

### Output is sorted deterministically

`core/parse/story/save.py` sorts all output dicts before writing (via `sort_dict` from `core/util.py`). This ensures stable output.

### `data/` and `hash/` are gitignored

The output directories `data/` and `hash/` are in `.gitignore` (except `core/data/`). These are build artifacts.
