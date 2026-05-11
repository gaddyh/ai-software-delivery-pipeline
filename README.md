# AI Software Delivery Pipeline

An AI-powered software delivery pipeline that uses autonomous agents to develop, test, and ship software automatically.

## Project Structure

```
ai-software-delivery-pipeline/
├── pyproject.toml
├── README.md
├── .env.example
├── examples/
│   └── run_shipping_once.py
├── artifacts/
│   └── runs/
├── src/
│   └── ai_delivery/
│       ├── models/
│       │   ├── task_spec.py
│       │   ├── generated_artifact.py
│       │   └── execution_result.py
│       ├── agents/
│       │   ├── orchestrator.py
│       │   ├── tester.py
│       │   └── developer.py
│       ├── execution/
│       │   └── pytest_runner.py
│       └── pipeline/
│           └── run_once.py
└── tests/
```

## Installation

```bash
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and configure your environment variables:

```bash
cp .env.example .env
```

## Usage

Run the shipping pipeline once:

```bash
python examples/run_shipping_once.py
```

## Components

- **Orchestrator Agent**: Coordinates the overall pipeline execution
- **Developer Agent**: Generates code based on task specifications
- **Tester Agent**: Writes and executes tests to validate generated code
- **Pytest Runner**: Executes pytest and captures results

## License

MIT
