import responses

from repo_analyzer.analyzer import GitHubRepoAnalyzer, parse_repo_spec


def test_parse_repo_spec_owner_name():
    assert parse_repo_spec("facebook/react") == ("facebook", "react")


def test_parse_repo_spec_url():
    assert parse_repo_spec("https://github.com/facebook/react") == ("facebook", "react")


def test_parse_repo_spec_url_with_git_suffix():
    assert parse_repo_spec("https://github.com/facebook/react.git") == ("facebook", "react")


@responses.activate
def test_analyze_basic_flow():
    owner, name = "octocat", "hello-world"

    responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{name}",
        json={
            "full_name": "octocat/hello-world",
            "description": "A test repo",
            "stargazers_count": 42,
            "forks_count": 5,
            "subscribers_count": 3,
            "open_issues_count": 2,
            "default_branch": "main",
            "license": {"spdx_id": "MIT"},
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "pushed_at": "2024-01-01T00:00:00Z",
            "size": 128,
            "archived": False,
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{name}/languages",
        json={"Python": 800, "Shell": 200},
        status=200,
    )
    responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{name}/contributors",
        json=[{"login": "octocat", "contributions": 100}],
        status=200,
    )
    responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{name}/commits",
        json=[
            {
                "sha": "abc1234567",
                "commit": {"message": "Initial commit", "author": {"date": "2024-01-01T00:00:00Z"}},
                "author": {"login": "octocat"},
            }
        ],
        status=200,
    )
    responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{name}/pulls",
        json=[],
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={"total_count": 1},
        status=200,
    )
    responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{name}/stats/commit_activity",
        json=[{"week": 1704067200, "total": 10, "days": [0, 1, 2, 3, 1, 2, 1]}],
        status=200,
    )
    responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{name}/stats/code_frequency",
        json=[[1704067200, 500, -100]],
        status=200,
    )
    responses.add(
        responses.GET,
        f"https://api.github.com/repos/{owner}/{name}/issues",
        json=[{"labels": [{"name": "bug"}]}],
        status=200,
    )

    analyzer = GitHubRepoAnalyzer(owner=owner, name=name, token="fake-token")
    report = analyzer.analyze()

    assert report.full_name == "octocat/hello-world"
    assert report.stars == 42
    assert report.language_percentages["Python"] == 80.0
    assert report.contributors[0]["login"] == "octocat"
    assert report.total_commits_last_year() == 10
    assert report.total_additions_last_year() == 500
    assert report.total_deletions_last_year() == 100
    assert report.open_pull_requests == 1
    assert report.top_issue_labels.get("bug") == 1
