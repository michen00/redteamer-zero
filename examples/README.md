# RedTeamer Zero Examples

This directory contains example scripts that demonstrate how to use the RedTeamer Zero framework.

## Getting Started

1. Make sure you have installed RedTeamer Zero in development mode:

   ```bash
   pip install -e .[dev]
   ```

2. Run the examples using Python:

   ```bash
   # Basic usage example
   python examples/basic_usage.py

   # Advanced usage example
   python examples/advanced_usage.py
   ```

## Example Descriptions

### Basic Usage (`basic_usage.py`)

This example demonstrates the most basic usage of the RedTeamer Zero framework, including:

- Setting up a simple policy
- Creating a basic scenario
- Running a red teaming experiment
- Interpreting the results

### Advanced Usage (`advanced_usage.py`)

This example shows more advanced usage, including:

- Creating custom attack strategies
- Implementing custom policy rules
- Working with more complex scenarios
- Handling different types of model outputs

## Extending the Examples

You can use these examples as a starting point for your own red teaming experiments. Here are some ideas:

1. **Custom Attack Strategies**: Implement your own attack strategies by extending the `BaseAttack` class.

2. **Custom Policy Rules**: Create specialized policy rules by extending the `PolicyRule` class.

3. **Integration with Real Models**: Replace the stub model with a real model implementation (e.g., OpenAI, Anthropic, etc.).

4. **Complex Scenarios**: Define more complex scenarios with multiple attack vectors and success criteria.

## Troubleshooting

If you encounter any issues while running the examples:

1. Make sure all dependencies are installed (check `pyproject.toml`).
2. Verify that you're using Python 3.10 or higher.
3. Check the console output for error messages.
4. If using a real model, ensure you have the necessary API keys and permissions.

For more information, refer to the [main documentation](../README.md) or [API reference](../API_REFERENCE.md).
