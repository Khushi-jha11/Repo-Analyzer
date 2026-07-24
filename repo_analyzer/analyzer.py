"""
Core logic for fetching and analyzing data about a GitHub repository.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import requests

GITHUB_API = "https://api.github.com"


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an error we can't recover from."""


@dataclass
class RepoReport:
    owner: str
    name: str
    full_name: str
    description: Optional[str]
    stars: int
    forks: int
    watchers: int
    open_issues: int
    default_branch: str
    license: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    pushed_at: Optional[str]
    size_kb: int
    is_archived: bool
    languages: dict[str, int] = field(default_factory=dict)
    language_percentages: dict[str, float] = field(default_factory=dict)
    contributors: list[dict[str, Any]] = field(default_factory=list)
    commit_activity: list[dict[str, Any]] = field(default_factory=list)
    code_frequency: list[list[int]] = field(default_factory=list)
    open_pull_requests: int = 0
    top_issue_labels: dict[str, int] = field(default_factory=dict)
    recent_commits: list[dict[str, Any]] = field(default_factory=list)

    def total_commits_last_year(self) -> int:
        return sum(week.get("total", 0) for week in self.commit_activity)

    def total_additions_last_year(self) -> int:
        return sum(week[1] for week in self.code_frequency if len(week) > 1)

    def total_deletions_last_year(self) -> int:
        return sum(abs(week[2]) for week in self.code_frequency if len(week) > 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner": self.owner,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "stars": self.stars,
            "forks": self.forks,
            "watchers": self.watchers,
            "open_issues": self.open_issues,
            "open_pull_requests": self.open_pull_requests,
            "default_branch": self.default_branch,
            "license": self.license,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "pushed_at": self.pushed_at,
            "size_kb": self.size_kb,
            "is_archived": self.is_archived,
            "languages": self.languages,
            "language_percentages": self.language_percentages,
            "contributors": self.contributors,
            "top_issue_labels": self.top_issue_labels,
            "total_commits_last_year": self.total_commits_last_year(),
            "total_additions_last_year": self.total_additions_last_year(),
            "total_deletions_last_year": self.total_deletions_last_year(),
            "recent_commits": self.recent_commits,
        }


class GitHubRepoAnalyzer:
    """Fetches and computes analytics for a single GitHub repository."""

    def __init__(self, owner: str, name: str, token: Optional[str] = None, timeout: int = 15):
        self.owner = owner
        self.name = name
        self.timeout = timeout
        self.token = token or os.environ.get("GITHUB_TOKEN")

        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repo-analyzer/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers.update(headers)

    # -- low level helpers -------------------------------------------------

    def _get(self, path: str, params: Optional[dict] = None, allow_202_retry: bool = True) -> Any:
        """GET a GitHub API path, handling rate limits and the 202 stats-computing case."""
        url = path if path.startswith("http") else f"{GITHUB_API}{path}"
        for attempt in range(6):
            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 202 and allow_202_retry:
                # GitHub is still computing stats (common for /stats/* endpoints
                # on repos that haven't been queried recently). Wait and retry.
                time.sleep(min(2 * (attempt + 1), 8))
                continue

            if response.status_code == 403 and "rate limit" in response.text.lower():
                reset = response.headers.get("X-RateLimit-Reset")
                wait = 5
                if reset:
                    wait = max(1, int(reset) - int(time.time()))
                raise GitHubAPIError(
                    f"GitHub API rate limit exceeded. Resets in ~{wait}s. "
                    "Set a GITHUB_TOKEN environment variable for higher limits."
                )

            if response.status_code == 404:
                raise GitHubAPIError(f"Not found: {url}. Check the owner/repo name and access rights.")

            if not response.ok:
                raise GitHubAPIError(f"GitHub API error {response.status_code} for {url}: {response.text[:200]}")

            if response.status_code == 204 or not response.content:
                return None

            return response.json()

        return None

    # -- individual data fetchers -------------------------------------------

    def fetch_repo_info(self) -> dict:
        return self._get(f"/repos/{self.owner}/{self.name}")

    def fetch_languages(self) -> dict:
        return self._get(f"/repos/{self.owner}/{self.name}/languages") or {}

    def fetch_contributors(self, limit: int = 10) -> list[dict]:
        data = self._get(
            f"/repos/{self.owner}/{self.name}/contributors",
            params={"per_page": limit, "anon": "false"},
        ) or []
        return [
            {"login": c.get("login", "unknown"), "contributions": c.get("contributions", 0)}
            for c in data[:limit]
        ]

    def fetch_commit_activity(self) -> list[dict]:
        # weekly commit counts for the last 52 weeks
        data = self._get(f"/repos/{self.owner}/{self.name}/stats/commit_activity") or []
        return data

    def fetch_code_frequency(self) -> list[list[int]]:
        # [week_timestamp, additions, deletions] for the life of the repo
        data = self._get(f"/repos/{self.owner}/{self.name}/stats/code_frequency") or []
        return data[-52:]  # keep it to roughly the last year for a fair comparison

    def fetch_open_pull_requests(self) -> int:
        data = self._get(
            f"/repos/{self.owner}/{self.name}/pulls",
            params={"state": "open", "per_page": 1},
        )
        # Cheap way to just get a count without paging through everything:
        # GitHub doesn't return a total count header for this endpoint, so we
        # fall back to the search API which does.
        search = self._get(
            "/search/issues",
            params={"q": f"repo:{self.owner}/{self.name} is:pr is:open"},
        )
        if search:
            return search.get("total_count", 0)
        return len(data) if data else 0

    def fetch_top_issue_labels(self, sample_size: int = 100) -> dict[str, int]:
        issues = self._get(
            f"/repos/{self.owner}/{self.name}/issues",
            params={"state": "open", "per_page": sample_size},
        ) or []
        label_counts: dict[str, int] = {}
        for issue in issues:
            if "pull_request" in issue:
                continue  # the issues endpoint also returns PRs; skip those
            for label in issue.get("labels", []):
                label_name = label.get("name") if isinstance(label, dict) else label
                if label_name:
                    label_counts[label_name] = label_counts.get(label_name, 0) + 1
        return dict(sorted(label_counts.items(), key=lambda kv: kv[1], reverse=True)[:10])

    def fetch_recent_commits(self, limit: int = 5) -> list[dict]:
        data = self._get(
            f"/repos/{self.owner}/{self.name}/commits",
            params={"per_page": limit},
        ) or []
        commits = []
        for c in data:
            commit_info = c.get("commit", {})
            author = commit_info.get("author", {}) or {}
            commits.append(
                {
                    "sha": c.get("sha", "")[:7],
                    "message": commit_info.get("message", "").splitlines()[0][:80],
                    "author": (c.get("author") or {}).get("login") or author.get("name", "unknown"),
                    "date": author.get("date"),
                }
            )
        return commits

    # -- orchestration -------------------------------------------------------

    def analyze(
        self,
        include_commit_activity: bool = True,
        include_code_frequency: bool = True,
        include_issue_labels: bool = True,
    ) -> RepoReport:
        info = self.fetch_repo_info()

        languages = self.fetch_languages()
        total_bytes = sum(languages.values()) or 1
        language_percentages = {
            lang: round(bytes_ / total_bytes * 100, 2) for lang, bytes_ in languages.items()
        }

        report = RepoReport(
            owner=self.owner,
            name=self.name,
            full_name=info.get("full_name", f"{self.owner}/{self.name}"),
            description=info.get("description"),
            stars=info.get("stargazers_count", 0),
            forks=info.get("forks_count", 0),
            watchers=info.get("subscribers_count", info.get("watchers_count", 0)),
            open_issues=info.get("open_issues_count", 0),
            default_branch=info.get("default_branch", "main"),
            license=(info.get("license") or {}).get("spdx_id") if info.get("license") else None,
            created_at=info.get("created_at"),
            updated_at=info.get("updated_at"),
            pushed_at=info.get("pushed_at"),
            size_kb=info.get("size", 0),
            is_archived=info.get("archived", False),
            languages=languages,
            language_percentages=language_percentages,
        )

        report.contributors = self.fetch_contributors()
        report.recent_commits = self.fetch_recent_commits()
        report.open_pull_requests = self.fetch_open_pull_requests()

        if include_commit_activity:
            report.commit_activity = self.fetch_commit_activity()
        if include_code_frequency:
            report.code_frequency = self.fetch_code_frequency()
        if include_issue_labels:
            report.top_issue_labels = self.fetch_top_issue_labels()

        return report


def parse_repo_spec(spec: str) -> tuple[str, str]:
    """Parse 'owner/name' or a full GitHub URL into (owner, name)."""
    spec = spec.strip()
    if spec.startswith("http://") or spec.startswith("https://"):
        spec = spec.split("github.com/", 1)[-1]
    spec = spec.rstrip("/")
    if spec.endswith(".git"):
        spec = spec[: -len(".git")]
    parts = spec.split("/")
    if len(parts) < 2:
        raise ValueError(f"Could not parse repository spec: {spec!r}. Expected 'owner/name'.")
    return parts[0], parts[1]
