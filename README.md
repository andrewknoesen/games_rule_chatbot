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

### Package release

For this we are simulating PyPi by hosting a page on github pages. This will be done on the branch `gh-pages`. Not this branch must never be manuall committed to and must only be done via the github action.

#### How to Enable GitHub Pages
	•	Go to your repository’s Settings > Pages (or “Code and automation” > “Pages”).
	•	Under Source, select your  gh-pages  branch (or whichever branch you’re using for the index).
	•	If prompted, choose the root ( / ) or the appropriate folder as the site directory.
	•	Save the changes. GitHub will provide a URL like  https://yourorg.github.io/yourrepo/  that you can use as your --extra-index-url  for pip installs.

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
