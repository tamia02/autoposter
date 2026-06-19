import subprocess
import os
from pathlib import Path
from datetime import datetime


def git_init_if_needed(repo_path: str = None):
    """Initialize git repo if not already initialized."""
    if repo_path is None:
        repo_path = Path.cwd()
    repo_path = Path(repo_path)
    git_dir = repo_path / '.git'
    if not git_dir.exists():
        subprocess.run(['git', 'init'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.email', 'routine@claude.local'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Claude Routine'], cwd=repo_path, check=True)


def git_commit_drafts(repo_path: str = None, topic: str = '', message: str = None) -> str:
    """Stage and commit draft files."""
    if repo_path is None:
        repo_path = Path.cwd()
    repo_path = Path(repo_path)

    drafts_dir = repo_path / 'drafts'
    if not drafts_dir.exists():
        return 'No drafts directory found.'

    # Stage drafts
    subprocess.run(['git', 'add', str(drafts_dir)], cwd=repo_path, check=True)

    # Commit
    if message is None:
        message = f"Auto-generated drafts: {topic} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    subprocess.run(['git', 'commit', '-m', message], cwd=repo_path, check=True)

    return f'Committed: {message}'


def git_create_branch(repo_path: str = None, branch_name: str = None) -> str:
    """Create and checkout a new branch."""
    if repo_path is None:
        repo_path = Path.cwd()
    repo_path = Path(repo_path)

    if branch_name is None:
        branch_name = f"drafts-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    subprocess.run(['git', 'checkout', '-b', branch_name], cwd=repo_path, check=True)
    return branch_name


def git_push_branch(repo_path: str = None, remote: str = 'origin', branch: str = None) -> str:
    """Push branch to remote."""
    if repo_path is None:
        repo_path = Path.cwd()
    repo_path = Path(repo_path)

    if branch is None:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_path, capture_output=True, text=True)
        branch = result.stdout.strip()

    subprocess.run(['git', 'push', '-u', remote, branch], cwd=repo_path, check=True)
    return f'Pushed {branch} to {remote}'


def git_create_pr(repo_path: str = None, title: str = '', body: str = '', branch: str = None) -> dict:
    """
    Create a PR (CLI-based; requires GitHub CLI or manual PR creation).
    This is a placeholder that returns a PR descriptor.
    For automation, install 'gh' CLI and uncomment the subprocess call.
    """
    if repo_path is None:
        repo_path = Path.cwd()
    repo_path = Path(repo_path)

    if branch is None:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_path, capture_output=True, text=True)
        branch = result.stdout.strip()

    # Placeholder: GitHub CLI integration (requires `gh` to be installed)
    # Uncomment the lines below if you have GitHub CLI set up:
    # subprocess.run(['gh', 'pr', 'create', '--title', title, '--body', body, '--head', branch], cwd=repo_path, check=True)

    return {
        'status': 'ready',
        'title': title,
        'body': body,
        'branch': branch,
        'next_step': 'Push branch and manually create PR on GitHub, or install GitHub CLI (`gh`) and use `gh pr create`.',
    }
