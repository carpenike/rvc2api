# Pull Request Guidelines

This document provides guidelines for creating and submitting pull requests to the CoachIQ project.

## Pull Request Workflow

```mermaid
flowchart TD
    Issue[Issue or Feature Request] --> Fork[Fork Repository]
    Fork --> Branch[Create Feature Branch]
    Branch --> Develop[Develop Changes]
    Develop --> QualityChecks{Quality Checks}
    QualityChecks -->|Pass| CreatePR[Create Pull Request]
    QualityChecks -->|Fail| Develop

    CreatePR --> CodeReview{Code Review}
    CodeReview -->|Approved| CIChecks{CI Checks}
    CodeReview -->|Changes Requested| UpdatePR[Update PR]
    UpdatePR --> CodeReview

    CIChecks -->|Pass| Merge[Merge PR]
    CIChecks -->|Fail| FixCI[Fix CI Issues]
    FixCI --> CIChecks

    Merge --> Release[Include in Release]

    classDef start fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef process fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;
    classDef decision fill:#fff8e1,stroke:#f9a825,stroke-width:1px;
    classDef end fill:#fce4ec,stroke:#c2185b,stroke-width:2px;

    class Issue start;
    class Fork,Branch,Develop,UpdatePR,FixCI process;
    class QualityChecks,CodeReview,CIChecks decision;
    class Merge,Release end;
```

## Pull Request Expectations

All pull requests should include:

- Tests for new logic and functionality
- Documentation updates (inline or markdown)
- Passing code quality checks:
  - Linting: `ruff check .`
  - Type checking: `pyright src`
  - Formatting: `ruff format src`
- Scoped, focused changes rather than monolithic updates
- References to design intent or research, if needed

## Pull Request Structure

When creating a pull request, please include the following sections:

### Problem Statement

Clearly describe the issue or requirement that the PR addresses. This helps reviewers understand the context and motivation for the changes.

### Solution Overview

Provide a high-level description of your solution approach. Explain key design decisions and trade-offs considered.

### Testing Strategy

Describe how you've tested the changes:

- What kinds of tests were added or updated
- How edge cases are covered
- Any manual testing that was performed

### Code Quality Verification

Explain the steps you've taken to ensure code quality:

- Confirmation that linting and type checking pass
- Any type stub additions or modifications that were necessary
- Formatting and style consistency measures

### Documentation Updates

Outline any documentation changes:

- API documentation updates
- New or updated markdown files
- Changes to inline documentation

### Related Issues

Link to any related GitHub issues that this PR addresses or impacts, using the GitHub issue linking syntax (e.g., "Fixes #123").

## Pull Request Review Process

1. Pull requests will be reviewed by at least one maintainer
2. Automated checks must pass (CI/CD)
3. All review comments must be addressed
4. Final approval requires passing CI and maintainer approval

## Tips for Successful Pull Requests

- **Keep changes focused**: Address one concern per PR
- **Provide context**: Help reviewers understand why changes are needed
- **Be responsive**: Address review feedback promptly
- **Update tests**: Ensure test coverage remains high
- **Document changes**: Update relevant documentation

For more detailed information about the project's code style and development practices, refer to:

- [Python Code Style](../python-code-style.md)
- [TypeScript Code Style](../typescript-code-style.md)
- [Pre-Commit Hooks](../pre-commit-and-actions.md)
