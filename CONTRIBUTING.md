# Contributing to AI Internship Agent

Thank you for your interest in contributing!

## Development Environment

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for local development)

### Setup

1. Fork the repository on GitHub.

2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/ai-internship-agent.git
   cd ai-internship-agent
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. Set up environment:
   ```bash
   cp .env.local.example .env
   # Edit .env with your settings
   ```

6. Start infrastructure:
   ```bash
   docker compose up -d postgres redis
   ```

7. Run migrations and seed data:
   ```bash
   python scripts/migrate.py
   python scripts/seed_demo.py
   ```

## Code Style

- Python: Follow PEP 8. Use `black` for formatting and `isort` for imports.
- TypeScript/JavaScript: Follow the project's ESLint configuration.
- Commit messages: Use Conventional Commits format (see below).

## Testing

Run all tests before submitting a PR:

```bash
# Backend tests
python -m pytest tests/unit tests/integration -q

# Frontend type check
cd frontend && npm run type-check
```

## Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes. Ensure all tests pass.

3. Commit using Conventional Commits:
   ```
   feat: add new tool for job matching
   fix: correct resume parsing error
   docs: update API documentation
   ```

4. Push to your fork and open a Pull Request.

5. Your PR will be reviewed by a maintainer. Address any feedback.

## Commit Message Format

```
<type>: <short description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## What to Contribute?

- Bug fixes
- New features (open an issue first to discuss)
- Documentation improvements
- Test coverage improvements
- Performance improvements

## Questions?

Feel free to open a GitHub Discussion if you have any questions.
