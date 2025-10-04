# RedTeamer Zero

> Advanced AI Safety Testing Framework

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/yourusername/redteamer-zero/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/redteamer-zero/actions)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://yourusername.github.io/redteamer-zero/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Overview

RedTeamer Zero is a comprehensive framework for testing and improving the safety and robustness of AI systems through automated red teaming. It implements a sophisticated Attacker-Defender-Judge-Learner loop to systematically identify and address vulnerabilities in AI models.

## ✨ Key Features

- **Automated Red Teaming**: Simulate sophisticated attacks to uncover model vulnerabilities
- **Defense Evaluation**: Test and compare different defense mechanisms
- **Comprehensive Metrics**: Track success rates, costs, and performance metrics
- **Reproducible Experiments**: Deterministic testing with configurable seeds and budgets
- **Extensible Architecture**: Easily plug in custom models, attacks, and defenses
- **Safety-First**: Built with responsible AI practices in mind

## 🛠️ Installation

```bash
# Ensure uv is available
pip install --upgrade uv

# Sync dependencies (creates .venv automatically)
uv sync

# Activate the environment when running outside uv (optional)
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Run commands through uv without activating the venv
uv run rtz --help
```

## 🚦 Quick Start

### Running a Basic Test

```bash
# Run a basic experiment with the stub model
uv run rtz run \
  --scenarios scenarios/basic/*.yaml \
  --policy policies/baseline.yaml \
  --model stub:echo \
  --budget.usd 0.10 \
  --seed 42 \
  --report out/run_$(date +%F)
```

### Example Output

```text
[INFO] Starting experiment with seed=42
[INFO] Running scenario: basic_prompt_injection
[INFO] Attempt 1/5: Defense applied, attack blocked
[INFO] Attempt 2/5: Defense bypassed, attack successful
[INFO] Generated report: out/run_2025-09-26/index.html
```

## 📂 Project Structure

```text
redteamer-zero/
├── src/rtz/                # Core package (src layout)
│   ├── attack/             # Attack strategies and payloads
│   ├── defense/            # Defense mechanisms and policies
│   ├── judge/              # Evaluation and scoring
│   ├── models/             # Model interfaces and adapters
│   ├── orchestration/      # LangGraph workflow definitions
│   ├── reports/            # Report generation
│   └── utils/              # Shared utilities (logging, cache, etc.)
├── scenarios/              # Basic and advanced test scenarios
├── policies/               # Baseline and strict guard policies
├── tests/                  # Test suite (pytest)
├── pyproject.toml          # Project metadata (uv-compatible)
└── README.md               # This file
```

## 🏗️ Core Concepts

### 1. Attack Vectors

- **Prompt Injection**: Attempt to bypass safety filters
- **Jailbreaking**: Try to make the model ignore its guidelines
- **Data Extraction**: Attempt to extract training data
- **Role Play**: Test for role-based vulnerabilities

### 2. Defense Mechanisms

- **Input Validation**: Filter malicious inputs
- **Output Filtering**: Sanitize model outputs
- **Prompt Engineering**: Design robust system prompts
- **Model-Specific Protections**: Leverage built-in safety features

### 3. Evaluation Metrics

- **Attack Success Rate (ASR)**: Percentage of successful attacks
- **False Positive Rate (FPR)**: Benign inputs incorrectly flagged
- **Cost Analysis**: Compute and memory usage
- **Time-to-Detection**: How quickly attacks are detected

## 🔍 Example Usage

### Running with Different Models

```bash
# With OpenAI
uv run rtz run --model openai:gpt-4 \
  --openai-api-key "$OPENAI_API_KEY"

# With Ollama
uv run rtz run --model ollama:llama3
```

### Custom Policy Testing

```yaml
# policies/strict_leak_guard.yaml
version: 1
name: strict-leak-guard
pre_input:
  - rule: deny-shadowed-prompts
    if:
      regex: ["(?i)system prompt", "(?i)hidden instruction"]
    then:
      action: block
      reason: prompt-leak-attempt
tool_call:
  - rule: allowlisted-tools-only
    if:
      tool_name_in: ["search", "stub"]
    then:
      action: allow
```

## 🧪 Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=rtz --cov-report=html

# Run specific test categories
uv run pytest tests/integration/
uv run pytest tests/benchmark/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

Comprehensive documentation is available to help you get the most out of RedTeamer Zero:

- [**Tutorial**](TUTORIAL.md) - Step-by-step uv workflow, scenarios, and policies
- [**API Reference**](API_REFERENCE.md) - Detailed documentation of all classes and methods
- [**Examples**](examples/) - Ready-to-run example scripts
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Scenarios](scenarios/) - Basic and advanced scenario collections

For the latest updates and discussions, visit our [GitHub Discussions](https://github.com/yourusername/redteamer-zero/discussions).

## 📈 Roadmap

- [ ] Support for more model providers
- [ ] Additional attack strategies
- [ ] Interactive visualization tools
- [ ] Pre-built policy templates
- [ ] Integration with MLflow/Weights & Biases
