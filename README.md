## Games Rule Chatbot

A chatbot that will be able to answer questions about games based on their rules.

### Project Structure

```
libs/           # Internal libraries
├── core        # Core business logic
├── mcp         # MCP server implementation
└── vector      # Vector database operations

infra/          # Infrastructure code
├── terraform/  # IaC configurations
└── kubernetes/ # K8s manifests
```

### Development

1. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

### Running Tests

```bash
pytest
```

### Deployment

See `infra/` directory for deployment configurations.