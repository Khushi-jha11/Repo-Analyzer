"""
GitHub Repository Analyzer.

A small toolkit for pulling analytics (stars, languages, contributors,
commit activity, issue labels, etc.) about any GitHub repository via the
GitHub REST API.
"""

from .analyzer import GitHubRepoAnalyzer, RepoReport, GitHubAPIError, parse_repo_spec

__version__ = "1.0.0"
__all__ = [
    "GitHubRepoAnalyzer",
    "RepoReport",
    "GitHubAPIError",
    "parse_repo_spec",
]
