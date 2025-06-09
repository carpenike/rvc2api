---
mode: "static"
description: "Index of available prompt templates for CoachIQ development"
---

# CoachIQ Prompt Templates

This directory contains prompt templates to help with various aspects of CoachIQ development. These templates are designed to work with GitHub Copilot Chat and other AI assistants to provide structured guidance for common development tasks.

## Available Prompts

### 📋 Planning & Specification

- [**Feature Planning Guide**](feature-planning.prompt.md) - Guide for planning a new feature by breaking it down into manageable components.

  - _Example scenario_: Planning a tank level monitoring feature that integrates with multiple sensor types.
  - _Example outcome_: A detailed feature plan in `/docs/specs/tank-monitoring.md` outlining data models, API endpoints, WebSocket events, and UI components needed.

- [**New Service Specification**](new-service-spec.prompt.md) - Template for defining a new service or feature before implementation.

  - _Example scenario_: Defining a new service to integrate with Victron Energy's Modbus protocol.
  - _Example outcome_: A comprehensive specification in `/docs/specs/victron-modbus-service.md` defining interfaces, data structures, and integration points.

- [**Architectural Decision Guide**](architectural-decision.prompt.md) - Framework for making and documenting architectural decisions.
  - _Example scenario_: Deciding how to handle WebSocket reconnection and state synchronization.
  - _Example outcome_: An ADR in `/docs/specs/adr-websocket-reconnection.md` analyzing options and documenting the chosen approach with implementation details.

### 🔧 Implementation & Development

- [**Feature Implementation Guide**](feature-implementation.prompt.md) - Step-by-step guide for implementing a new feature following project patterns.

  - _Example scenario_: Implementing the tank monitoring feature based on the existing specification.
  - _Example outcome_: Structured implementation with proper data models, API endpoints, and test coverage following project patterns.

- [**RV-C Integration Guide**](rvc-integration.prompt.md) - Specific guidance for adding support for new RV-C DGNs and functionality.

  - _Example scenario_: Adding support for the RV-C DC Dimmer Commands (DGN 0x1FEDD).
  - _Example outcome_: A detailed implementation plan in `/docs/specs/rvc-dgn-0x1FEDD.md` that outlines decoder changes, device mapping, and API integration.

- [**Code Refactoring Guide**](code-refactoring.prompt.md) - Framework for planning and executing code refactoring tasks.

  - _Example scenario_: Refactoring the state management system to improve performance and reliability.
  - _Example outcome_: A comprehensive refactoring plan in `/docs/specs/refactor-state-management.md` with step-by-step changes and testing strategy.

- [**React UI Prototype Guide**](react-ui-prototype.prompt.md) - Guide for designing and implementing React components for the web interface.
  - _Example scenario_: Designing a React-based dashboard component for the new UI.
  - _Example outcome_: A detailed component specification in `/docs/specs/react-dashboard.md` with props interface, state management, API integration, and example code.

### 📝 Documentation

- [**Service Documentation Template**](service-documentation.prompt.md) - Comprehensive template for documenting a service component.
  - _Example scenario_: Creating thorough documentation for the HVAC control service after implementation.
  - _Example outcome_: A comprehensive documentation file that includes API details, data models, usage examples, configuration options, and troubleshooting tips.

### 🔍 Research & Exploration

- [**Protocol Research Guide**](protocol-research.prompt.md) - Framework for researching RV protocols, hardware interfaces, or features.
  - _Example scenario_: Researching the Victron Energy VE.Direct protocol for potential integration.
  - _Example outcome_: A detailed research document outlining protocol specifications, message formats, hardware requirements, and implementation recommendations.

## Using These Prompts

These prompt templates can be used in several ways:

1. **Direct Copy/Paste**: Copy the content of a prompt and paste it into a conversation with GitHub Copilot Chat or another AI assistant.

2. **Reference in Issues/PRs**: Link to these prompts in GitHub issues or pull requests to provide context for discussions.

3. **Customization**: Create a copy of a relevant prompt and customize it for your specific needs before using it.

## Workflow Example

Here's an example workflow using these prompts:

1. **Research**: Use the **Protocol Research Guide** to understand the Victron VE.Direct protocol.

   ```
   @copilot I need to research the Victron VE.Direct protocol. Let's use the Protocol Research Guide.
   ```

2. **Plan**: Use the **New Service Specification** template to define a VE.Direct integration service.

   ```
   @copilot I want to plan a new service for Victron VE.Direct integration. Let's use the New Service Specification template.
   ```

3. **Design**: Use the **Architectural Decision Guide** to decide on the integration approach.

   ```
   @copilot I need to decide on the architecture for VE.Direct integration. Let's use the Architectural Decision Guide.
   ```

4. **Implement**: Use the **Feature Implementation Guide** to implement the service.

   ```
   @copilot I'm ready to implement the VE.Direct service based on our spec in /docs/specs/victron-direct-service.md. Let's use the Feature Implementation Guide.
   ```

5. **Document**: Use the **Service Documentation Template** to document the new service.

   ```
   @copilot Now that the VE.Direct service is implemented, let's document it with the Service Documentation Template.
   ```

## MCP Tools Integration

These prompts work well with the MCP tools defined in the project:

- Use `@context7` with these prompts to get project-specific recommendations based on the current codebase.

  - _Example_: `@context7 Show me how WebSocket connections are currently implemented` will help when designing new WebSocket features.

- Use `@perplexity` for researching external protocols or libraries mentioned in your planning.

  - _Example_: `@perplexity What is the message format for Victron VE.Direct protocol?` will provide external knowledge.

- Use `@github` to find related issues or PRs while planning new features.
  - _Example_: `@github Search for issues related to tank monitoring` will find existing discussions on the topic.

## Planning to Implementation Flow

The prompts are designed to support a complete development workflow:

1. **Planning prompts** generate comprehensive specifications saved to `/docs/specs/<feature-name>.md`
2. **Implementation prompts** reference these specs for structured implementation
3. **Documentation prompts** ensure the feature is well-documented for future reference

This flow ensures consistent quality and maintainability throughout the development process.

## Prompt Relationships and Output Locations

The prompts follow consistent naming patterns for output files in the `/docs/specs/` directory:

| Prompt Template           | Output Location                         |
| ------------------------- | --------------------------------------- |
| feature-planning.md       | `/docs/specs/<feature-name>.md`         |
| new-service-spec.md       | `/docs/specs/<service-name>.md`         |
| architectural-decision.md | `/docs/specs/adr-<decision-topic>.md`   |
| code-refactoring.md       | `/docs/specs/refactor-<topic>.md`       |
| rvc-integration.md        | `/docs/specs/rvc-dgn-<dgn_number>.md`   |
| react-ui-prototype.md     | `/docs/specs/react-<component-name>.md` |

### Differences Between Similar Prompts

- **Feature Planning vs. New Service Spec**:

  - _Feature Planning_ focuses on breaking down an entire feature across multiple system components
  - _New Service Spec_ focuses on a single service and its detailed internal design

- **Feature Planning vs. RV-C Integration**:

  - _Feature Planning_ is general-purpose for any feature
  - _RV-C Integration_ is specialized for protocol-specific DGN implementations with byte-level details

- **Architectural Decision vs. Code Refactoring**:
  - _Architectural Decision_ focuses on making and documenting high-level design choices
  - _Code Refactoring_ focuses on restructuring existing code with minimal functional changes

## Contributing

If you have suggestions for improving these prompts or ideas for new ones, please submit a PR with your changes.

## Prompt YAML Front Matter

All prompt files include standardized front matter headers to provide metadata and enable special functionality:

```yaml
---
mode: "agent" # Indicates this is an interactive agent prompt
description: "Brief description of what the prompt does"
tools: ["context7", "perplexity_ask"] # Required tools for this prompt
---
```

### Front Matter Fields

- **mode**: Either 'agent' for interactive prompts or 'static' for reference files
- **description**: Brief summary of the prompt's purpose
- **tools**: List of MCP tools required for the prompt to function properly

### Using Context7 for Validation

Most planning prompts now include specific guidance to use `@context7` to validate approaches:

1. **Before specifying implementation details**:

   ```
   @context7 How are API endpoints structured in the current codebase?
   ```

2. **When choosing design patterns**:

   ```
   @context7 What patterns are used for WebSocket event handling?
   ```

3. **When integrating with existing components**:

   ```
   @context7 Show me how the state management system currently works
   ```

Always check existing code patterns using `@context7` before finalizing design decisions to maintain consistency across the codebase.
