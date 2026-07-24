# GitHub Repository Analyzer

A command-line tool that pulls together analytics for any public (or
accessible private) GitHub repository: stars/forks, language breakdown,
top contributors, commit activity, code churn, open-issue labels, and
recent commits — as a console report, Markdown file, JSON, or PNG charts.

## Features

- **Repo overview** — stars, forks, watchers, open issues/PRs, license, size, archive status
- **Language breakdown** — percentage of each language by bytes
- **Contributors** — top contributors ranked by commit count
- **Commit activity** — weekly commit counts for the last ~52 weeks
- **Code churn** — lines added/deleted over the last ~52 weeks
- **Issue labels** — most common labels on open issues
- **Recent commits** — the last few commits with author and message
- **Multiple output formats** — console (default), Markdown, JSON
- **Optional charts** — language pie chart, commit activity bar chart, contributor leaderboard (requires matplotlib)

## Installation

```bash
git clone https://github.com/yourusername/repo-analyzer.git
cd repo-analyzer
pip install -r requirements.txt
```

Or install it as a CLI command:

```bash
pip install .
# then run it anywhere as:
repo-analyzer facebook/react
```

## Usage

```bash
# Basic console report
python -m repo_analyzer facebook/react

# Works with a full URL too
python -m repo_analyzer https://github.com/facebook/react

# Markdown report saved to a file
python -m repo_analyzer facebook/react --format markdown --output report.md

# JSON output (handy for piping into other tools)
python -m repo_analyzer facebook/react --format json --output report.json

# Generate PNG charts alongside the report
python -m repo_analyzer facebook/react --charts --charts-dir ./charts
```

### Authentication

GitHub's unauthenticated API rate limit is low (60 requests/hour) and this
tool makes several requests per repo. Set a
[personal access token](https://github.com/settings/tokens) (no special
scopes needed for public repos) to raise that limit to 5,000/hour:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
python -m repo_analyzer facebook/react
```

or pass it directly with `--token ghp_xxxx`.

### All options

```
usage: repo-analyzer [-h] [--format {console,markdown,json}] [--output OUTPUT]
                      [--token TOKEN] [--charts] [--charts-dir CHARTS_DIR]
                      [--skip-commit-activity] [--skip-code-frequency]
                      [--skip-issue-labels]
                      repo
```

## Example output

```
============================================================
 octocat/Hello-World
 My first repository on GitHub!
============================================================
Stars: 2,847   Forks: 2,502   Watchers: 1,412   Open issues: 828   Open PRs: 502
License: none   Default branch: master   Size: 1 KB   Archived: False
Created: 2011-01-26   Last push: 2024-06-01

Languages:
  (no language data available for this repo)

Top contributors:
  octocat              1 commits
============================================================
```

## Using it as a library

```python
from repo_analyzer import GitHubRepoAnalyzer

analyzer = GitHubRepoAnalyzer(owner="facebook", name="react", token="ghp_xxx")
report = analyzer.analyze()

print(report.stars, report.language_percentages)
```

## Project layout

```
repo-analyzer/
├── repo_analyzer/
│   ├── __init__.py       # public API exports
│   ├── __main__.py       # `python -m repo_analyzer` entry point
│   ├── analyzer.py       # GitHub API client + data model
│   ├── report.py         # console / markdown / json renderers
│   ├── charts.py         # optional matplotlib charts
│   └── cli.py            # argparse-based CLI
├── tests/
│   └── test_analyzer.py
├── requirements.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

## Running tests

```bash
pip install -r requirements.txt pytest responses
pytest tests/
```

## License

MIT — see [LICENSE](LICENSE).
