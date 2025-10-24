# Contributing to RedTeamer Zero

Thank you for your interest in contributing to RedTeamer Zero! We welcome all forms of contributions, including bug reports, feature requests, documentation improvements, and code contributions.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Making Changes](#-making-changes)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Code Style](#-code-style)
- [Pull Request Process](#-pull-request-process)
- [Reporting Issues](#-reporting-issues)
- [License](#-license)

## Code of Conduct

This project adheres to the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally

   ```bash
   git clone https://github.com/yourusername/redteamer-zero.git
   cd redteamer-zero
   ```

3. **Set up the development environment** (see below)
4. **Create a new branch** for your changes

   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

1. **Set up a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install development dependencies**

   ```bash
   pip install -e .[dev]
   ```

3. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

## ✨ Making Changes

1. **Follow the branch naming convention**:
   - `feature/` for new features
   - `fix/` for bug fixes
   - `docs/` for documentation changes
   - `refactor/` for code refactoring
   - `test/` for test-related changes

2. **Write clear commit messages**:

   ```
   type(scope): short description

   More detailed description if needed.

   Fixes #issue-number
   ```

   Common types:
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style changes
   - `refactor`: Code refactoring
   - `test`: Test-related changes
   - `chore`: Maintenance tasks

## 🧪 Testing

We use `pytest` for testing. Before submitting a PR, please ensure:

1. All tests pass:

   ```bash
   pytest
   ```

2. Code coverage is maintained or improved:

   ```bash
   pytest --cov=rtz --cov-report=term-missing
   ```

3. Type checking passes:

   ```bash
   mypy rtz/
   ```

## 📚 Documentation

- Update relevant documentation when adding new features or changing behavior
- Follow the existing documentation style
- Add docstrings to all public functions and classes
- Update the README if necessary

## 🎨 Code Style

We use:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

These are enforced through pre-commit hooks. To run them manually:

```bash
black .
isort .
flake8
mypy rtz/
```

## 🔄 Pull Request Process

1. Ensure your fork is up to date with the main branch:

   ```bash
   git pull --rebase upstream main
   ```

2. Push your changes to your fork:

   ```bash
   git push origin your-branch-name
   ```

3. Open a pull request against the main branch

4. Ensure all CI checks pass

5. Request reviews from maintainers

6. Address any review feedback

## 🐛 Reporting Issues

When reporting issues, please include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Environment details (Python version, OS, etc.)
- Any relevant logs or error messages

## 📄 License

By contributing to RedTeamer Zero, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
