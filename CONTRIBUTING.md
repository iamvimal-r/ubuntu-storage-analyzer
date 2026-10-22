# Contributing to Ubuntu Storage & Memory Analyzer

Thank you for taking the time to contribute! 🎉

This document explains how to set up a development environment, follow the project's code style, and submit a pull request.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Branch Naming](#branch-naming)
- [Commit Message Style](#commit-message-style)
- [Code Style](#code-style)
- [Running Tests](#running-tests)
- [Pull Request Checklist](#pull-request-checklist)

---

## Code of Conduct

Be respectful and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) standard.

---

## How Can I Contribute?

- 🐛 **Bug reports** — Open an [issue](../../issues) with the bug report template
- 💡 **Feature requests** — Open an [issue](../../issues) with the feature request template
- 🔧 **Code fixes or features** — Fork → Branch → PR (see below)
- 📝 **Documentation improvements** — Fix typos, add examples, improve clarity
- 🧪 **Tests** — Add missing test coverage

---

## Development Setup

```bash
# 1. Fork the repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/ubuntu-storage-analyzer.git
cd ubuntu-storage-analyzer

# 2. Add the upstream remote
git remote add upstream https://github.com/iamvimal-r/ubuntu-storage-analyzer.git

# 3. Install system dependencies (Ubuntu)
sudo apt install -y python3 python3-venv libgl1 libxcb-cursor0 \
    libxcb-xinerama0 libxkbcommon-x11-0

# 4. Set up Python venv
bash setup.sh
source venv/bin/activate

# 5. Install dev extras (linting)
pip install flake8 pytest
```

Keep your fork in sync:

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

---

## Branch Naming

| Type | Pattern | Example |
|---|---|---|
| New feature | `feature/<short-description>` | `feature/remote-scan` |
| Bug fix | `fix/<short-description>` | `fix/scan-crash-symlink` |
| Documentation | `docs/<short-description>` | `docs/add-contributing` |
| Refactor | `refactor/<short-description>` | `refactor/alert-service` |
| Tests | `test/<short-description>` | `test/storage-scanner` |

---

## Commit Message Style

We use **Conventional Commits**:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or fixing tests |
| `chore` | Build process, dependency updates |
| `style` | Formatting, whitespace (no logic change) |

**Examples:**

```
feat(storage): add minimum file size filter
fix(alerts): prevent duplicate notifications on rapid threshold breach
docs(readme): add systemd service installation steps
test(scanner): add test for inode deduplication
```

---

## Code Style

- **Python version**: 3.9+ compatible
- **Formatter**: Keep lines ≤ 100 characters
- **Type hints**: Use them for all public function signatures
- **Docstrings**: Module-level docstring on every new file
- **No `shell=True`**: All subprocess calls must use argument lists
- **No bare `except`**: Always catch specific exception types
- **Imports**: Standard library → third-party → local, separated by blank lines

Lint check before committing:

```bash
flake8 . --max-line-length=100 --exclude=venv,__pycache__,.pytest_cache
```

---

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

All tests must pass before opening a PR. Add tests for any new behaviour you introduce.

---

## Pull Request Checklist

Before submitting, please verify:

- [ ] My branch is up-to-date with `main` (`git fetch upstream && git merge upstream/main`)
- [ ] All existing tests pass: `python -m pytest tests/ -v`
- [ ] I added tests for new behaviour
- [ ] My code follows the style guide (no `flake8` errors)
- [ ] I updated `CHANGELOG.md` under `[Unreleased]`
- [ ] The PR description explains *what* and *why*, not just *how*
- [ ] Screenshots or a short demo GIF are included if the UI changed

---

Thank you for contributing! 🙌
