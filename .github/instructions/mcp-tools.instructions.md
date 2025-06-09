---
applyTo: "**"
---

# Model Context Protocol (MCP) Tools

> **Note**: This file provides an overview of MCP tools for the project. For domain-specific examples, see the tool recommendation sections in the respective instruction files (code-style, testing, env-vars, react-frontend).

MCP tools provide context-aware AI assistance. They are integrated into GitHub Copilot Chat and can help you understand the codebase, research related topics, and navigate project repositories.

> **Important**: Always default to `@context7` for any library or framework questions before falling back to LLM-generated answers. This ensures you get current, correct API information rather than outdated or hallucinated answers.

## When to Prioritize Context7

Always use Context7 for these scenarios:

### Working with External Libraries

```
@context7 how to use FastAPI dependency injection
@context7 React useState with TypeScript generics
@context7 tailwind responsive design patterns
```

### Version-Specific Features

```
@context7 Next.js 14 App Router middleware
@context7 React 18 concurrent mode features
@context7 Python 3.12 typing features
```

### Library API Questions

```
@context7 FastAPI WebSocket authentication
@context7 React useCallback correct dependencies
@context7 tailwind dark mode configuration
```

### Example Code Requirements

```
@context7 FastAPI WebSocket broadcast example
@context7 React custom hook for websocket
@context7 tailwind responsive navbar example
```

## Overview of Available Tools

### @context7

Project-aware code lookups that deliver up-to-date, version-specific documentation and code examples:

- **Core functionality**: Find implementations, understand patterns, reference API schemas, and get current API documentation
- **Critical advantages**:
  - Provides up-to-date code examples (not limited to LLM training data)
  - Avoids hallucinated APIs that don't exist
  - Delivers version-specific documentation directly in context
- **When to use**:
  - Working with external libraries and frameworks (Next.js, React, FastAPI, etc.)
  - Implementing specific APIs or patterns
  - Learning how to use libraries with correct, current syntax
  - Ensuring code examples match the versions used in the project

### @perplexity

External research for protocols, libraries, and best practices:

- **Core functionality**: Search the web for technical information relevant to your task
- **When to use**: When you need information not found in the codebase (protocols, libraries, techniques)

### @github

Repository and issue information queries:

- **Core functionality**: Search repositories, issues, pull requests, and documentation
- **When to use**: To find related issues, check project history, or reference GitHub resources

## @github Examples

```
# Search for issues related to WebSocket reconnection
@github issues:CoachIQ+websocket+reconnection

# Find pull requests related to the React migration
@github pr:CoachIQ+react+frontend

# Get repository statistics
@github repo:CoachIQ stats

# Search for code examples in related repositories
@github code:python-can+socketcan+send
```

## Integrated Research Workflow

For most development tasks, follow this pattern:

1. **Get up-to-date library documentation**: Use `@context7` first for any library-related tasks

   ```
   @context7 next.js app router implementation
   @context7 fastapi websocket authentication
   @context7 react useEffect cleanup pattern version 18
   ```

2. **Explore the codebase**: Use `@context7` to find relevant code patterns in our project

   ```
   @context7 similar functionality to what I'm building
   @context7 websocket connection handling in core_daemon
   ```

3. **Research external information**: Use `@perplexity` for general best practices

   ```
   @perplexity technical approach for solving this problem
   ```

4. **Check project history**: Use `@github` to find related issues/PRs

   ```
   @github issues related to this component
   ```

5. **Document your sources**: Reference findings in code comments and PR descriptions

> **Important**: Always default to `@context7` for any library or framework questions before falling back to LLM-generated answers. This ensures you get current, correct API information rather than outdated or hallucinated answers.
