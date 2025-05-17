---
applyTo: "**"
---

# Pull Request Expectations

- Tests for new logic
- Docs (inline or markdown) updated
- All code quality checks pass:
  - Linting (`ruff check .`)
  - Type checking (`pyright src`)
  - Formatting (`ruff format src`)
- Scoped, focused change
- Reference design intent or research if needed

## PR Structure

- Problem statement
- Solution overview
- Testing strategy
- Code quality verification:
  - Explain steps taken to verify linting & type checking pass
  - Note any type stub additions or modifications
- Documentation updates
- Related issues (link GitHub issues)
