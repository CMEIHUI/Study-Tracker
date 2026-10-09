# Study Tracker

Study Tracker is a polished Python desktop application designed to help students organize subjects, tasks, study sessions, and achievement-driven productivity.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Backup and Restore](#backup-and-restore)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

Study Tracker Pro combines student planning, task tracking, study sessions, and analytics into a single modular application. It helps students stay focused with task planning, streak tracking, and achievement progress.

## Key Features

- User authentication and secure password hashing
- Subject creation and management
- Task creation, editing, deadlines, priorities, progress tracking, and subtasks
- Study session timer and tracking with daily and weekly summaries
- Calendar and deadline management
- Dashboard analytics with streaks and achievements
- Backup and restore support for SQLite data
- Centralized error handling and logging

## Architecture

The app follows a modular structure:

- `main.py` — startup, logging, and settings initialization
- `auth.py` — authentication and user management
- `dashboard.py` — main dashboard and page navigation
- `task.py`, `subject.py`, `calendar_page.py` — UI pages for core workflows
- `python/database/` — SQLite persistence, schema migrations, backup, and restore
- `ai_service.py` / `ai_analysis.py` — study analytics and scoring
- `utils.py` — shared validation, error handling, threading, and formatting helpers

## Installation

1. Install Python 3.13 or later.
2. Create a virtual environment:

```powershell
python -m venv .venv
```

3. Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Usage

Launch the application with:

```powershell
python main.py
```

## Backup and Restore

Study Tracker Pro includes native database backup and restore helpers.

### Backup

```python
from database import backup_database
backup_path = backup_database("studytracker.db")
```

### Restore

```python
from database import restore_database
restore_database("studytracker.db", "studytracker_backup_20260722_123456.db")
```

## Testing

Run the test suite:

```powershell
python -m unittest discover -s tests
```

If your Python installation does not include a working Tk/Tcl runtime, GUI tests may be skipped automatically because they require `tkinter` support.

## Project Structure

- `auth.py` — authentication flows
- `dashboard.py` — dashboard view, cards, and gamification
- `task.py` — task creation, editing, and list management
- `subject.py` — subject management UI
- `timer.py` — study timer implementation
- `calendar_page.py` — calendar interface
- `analytics.py` — stats and analytics visualization
- `report.py` — report generation
- `python/database/` — SQLite data layer and backup/restore
- `tests/` — automated tests
- `utils.py` — validation, logging, threading helpers

## Contributing

Contributions are welcome. Keep new features modular and compatible with the existing dashboard/page architecture.

## License

This project is distributed under the MIT License.
