---
mode: 'agent'
description: 'Template for documenting and guiding architectural decisions'
tools: ['context7']
---

# Architectural Decision Record (ADR) Template

This template guides you in making and documenting a single architectural decision for the rvc2api project. Each ADR should be clear, focused, and traceable, providing enough context and rationale for future reference and team alignment. Save the completed ADR to `/docs/specs/adr-<decision-topic>.md` (e.g., `adr-event-driven-messaging.md`).

---

## Metadata

- **Title:** [Concise decision name, e.g., "Adopt Event-Driven Messaging"]
- **Status:** [Proposed | Accepted | Rejected | Superseded]
- **Date:** [YYYY-MM-DD]
- **Version:** [e.g., 1.0]
- **Author(s):** [Name(s)]
- **Approver(s):** [Name(s), if applicable]

---

## 1. Context and Problem Statement

- **Background:**  
  Briefly describe the business or technical context that led to this decision.
- **Problem/Opportunity:**  
  What architectural challenge or opportunity does this ADR address?
- **Relevant Requirements:**  
  List key functional and non-functional requirements (e.g., scalability, maintainability, performance).
- **Current State:**  
  Summarize the current architecture and constraints. Use `@context7` for code analysis if needed.

---

## 2. Decision Drivers

- What factors are most important in making this decision?  
  (e.g., business goals, technical constraints, team expertise, regulatory requirements)

---

## 3. Considered Options

For each option, provide:

- **Option Name:**  
  - **Description:**  
    Briefly explain the approach.
  - **Pros:**  
    - [Advantage 1]
    - [Advantage 2]
  - **Cons:**  
    - [Disadvantage 1]
    - [Disadvantage 2]
  - **Implementation Complexity:** [Low | Medium | High]
  - **Long-term Maintenance:**  
    Briefly describe implications.

(Duplicate this section for each option you wish to document.)

---

## 4. Decision Outcome

- **Chosen Option:**  
  Clearly state which option is selected.
- **Rationale:**  
  Explain why this option was chosen over the alternatives, referencing decision drivers.
- **Confidence Level:** [High | Medium | Low]  
  (Optional, but recommended for transparency.)

---

## 5. Consequences

- **Positive Impacts:**  
  - [Benefit 1]
  - [Benefit 2]
- **Negative Impacts / Trade-offs:**  
  - [Drawback 1]
  - [Drawback 2]
- **Follow-up Actions:**  
  List any required next steps, additional ADRs, or review plans.

---

## 6. Implementation Plan

- **Phases and Milestones:**  
  Outline the steps or phases for implementation, with dependencies if relevant.
- **Migration Path:**  
  How will the transition from the current state occur? Is this a breaking change?
- **Affected Components:**  
  List major files, modules, or APIs impacted.

---

## 7. Validation and Testing

- **Validation Approach:**  
  How will you confirm the decision meets requirements?
- **Testing Strategy:**  
  What tests are needed (unit, integration, performance, etc.)?

---

## 8. Risks and Mitigations

- **Identified Risks:**  
  - [Risk 1]
  - [Risk 2]
- **Mitigation Strategies:**  
  - [Mitigation 1]
  - [Mitigation 2]

---

## 9. References

- **Internal References:**  
  Link to related ADRs, code, or documentation.
- **External References:**  
  Cite relevant standards, articles, or best practices.

---

> **Note:**  
> Each ADR should address a single architectural decision. Update the status as the decision progresses (Proposed, Accepted, Rejected, Superseded). Keep records concise, assertive, and factual. For broader design guides or ideation, link to supplemental documentation.
