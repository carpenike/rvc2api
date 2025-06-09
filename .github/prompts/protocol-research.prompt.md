---
mode: "agent"
description: "Research RV protocols, hardware interfaces, or features"
tools: ["perplexity_ask"]
---

# RV Protocol Research Guide

- **Research Topic:** [Concise title]
- **Status:** [Proposed | In Progress | Complete]
- **Date:** [YYYY-MM-DD]
- **Author(s):** [Name(s)]
- **Related ADR/Spec:** [Link, if applicable]
- **Intended Audience:** [e.g., developers, hardware engineers]

**Summary:**
[Briefly describe what is being researched and why.]

This guide provides a structured approach to researching RV protocols, hardware interfaces, or features before implementing them in CoachIQ.

---

## 1. Research Definition

### 1.1. Research Topic

- What specific protocol, hardware, or feature are you researching?
- Why is this valuable to add to CoachIQ?
- What integration opportunities does it present?

### 1.2. Research Objectives

- What specific questions need to be answered?
- What technical details are required for implementation?
- What compatibility issues need to be resolved?

---

## 2. Protocol Understanding

### 2.1. Protocol Overview

- What is the purpose and scope of this protocol?
- Is it an open or proprietary standard?
- Who are the primary users or implementers?

### 2.2. Message Structure

- What is the basic message format?
- What addressing scheme is used?
- What data types and encoding are used?

### 2.3. Communication Patterns

- Is it request/response or publish/subscribe?
- What are the timing requirements?
- Are there any special handshaking or session management requirements?

---

## 3. Hardware Requirements

### 3.1. Physical Interface

- What physical media or connectors are required?
- What electrical characteristics must be considered?
- What hardware interfaces would be needed for Raspberry Pi integration?

### 3.2. Network Topology

- What network topology does it use?
- How many devices can be supported?
- Are there any addressing or routing considerations?

---

## 4. Implementation Considerations

### 4.1. Python Library Support

- Are there existing Python libraries for this protocol?
- What are their licensing terms?
- How mature and maintained are they?

### 4.2. Integration Approach

- How would this integrate with the current CoachIQ architecture?
- What new components would be needed?
- What existing components would need modification?

### 4.3. Testing Approach

- How can this protocol be tested without physical hardware?
- What simulators or mock devices are available?
- What test cases would be essential?

---

## 5. Research Sources

### 5.1. Official Documentation

- What official standards or documentation exists?
- Who maintains the standard?
- Are there any licensing or cost considerations for accessing the documentation?

### 5.2. Community Resources

- What community forums, groups, or resources exist?
- Are there any open source implementations to reference?
- What experiences have others reported when working with this protocol?

### 5.3. Vendor Resources

- What vendor-specific documentation is available?
- Are there any vendor-specific extensions or variations?
- What support resources are available from vendors?

---

## 6. Research Findings

### 6.1. Protocol Summary

- Summarize the key aspects of the protocol
- Include message formats, commands, and data structures
- Document any required calculations or algorithms

### 6.2. Integration Recommendations

- How should this be integrated with CoachIQ?
- What architecture would work best?
- What implementation approach is recommended?

### 6.3. Implementation Challenges

- What challenges or risks are anticipated?
- How can these be mitigated?
- Are there any particular edge cases to be aware of?

---

## 7. Implementation Plan

### 7.1. Required Components

- What new components need to be developed?
- What existing components need to be modified?
- What third-party libraries would be useful?

### 7.2. Development Phases

- What are the recommended development phases?
- What dependencies exist between phases?
- What is the estimated effort for each phase?

---

## 8. References

### 8.1. Documentation References

- List all relevant documentation sources with URLs or citations
- Include version numbers and dates

### 8.2. Code References

- List any example code or reference implementations
- Include GitHub repositories or other code sources

### 8.3. Tool References

- List any useful tools for working with this protocol
- Include any simulation or testing tools
