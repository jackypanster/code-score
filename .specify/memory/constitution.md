<!--
Sync Impact Report:
Version change: [new] → 1.0.0
Added sections: All principles and governance sections (initial creation)
Modified principles: None (initial creation)
Removed sections: None
Templates requiring updates: ⚠ Manual review needed for dependent templates
Follow-up TODOs: None
-->

# Code Score Constitution

## Core Principles

### I. UV-Based Dependency Management
All Python dependencies and virtual environments MUST be managed through `uv`. No exceptions for pip, conda, or other package managers. This ensures consistent, fast, and reproducible builds across all environments.

**Rationale**: UV provides superior performance and reliability for Python dependency management. Standardizing on a single tool eliminates environment inconsistencies and reduces onboarding complexity.

### II. KISS Principle (Keep It Simple, Stupid)
Code MUST prioritize simplicity over cleverness. Avoid over-engineering, excessive abstractions, and premature optimization. When encountering errors or exceptional conditions, programs MUST immediately throw exceptions and halt execution rather than attempting complex error recovery.

**Rationale**: Simple code is more maintainable, debuggable, and reliable. Failing fast prevents cascading errors and makes debugging significantly easier.

### III. Transparent Change Communication
Every code modification MUST be accompanied by clear documentation of what changed and why. This includes commit messages, pull request descriptions, and any relevant design decisions.

**Rationale**: Understanding the motivation behind changes is crucial for maintaining code quality over time and enables effective collaboration.

## Development Workflow

### Error Handling Standards
- Exceptions MUST be thrown immediately upon detection
- No silent failures or error suppression
- Use specific exception types rather than generic ones
- Include meaningful error messages with context

### Code Review Requirements
- All changes MUST explain what was modified and the reasoning
- Reviews MUST verify adherence to KISS principle
- Dependencies MUST use uv exclusively

## Quality Standards

### Simplicity Metrics
- Functions SHOULD have a single responsibility
- Classes SHOULD be focused and cohesive
- Avoid deep inheritance hierarchies
- Prefer composition over inheritance

### Documentation Requirements
- README MUST include uv setup instructions
- All public APIs MUST have clear documentation
- Change logs MUST explain both what and why

## Governance

This constitution supersedes all other development practices. All code reviews, pull requests, and architecture decisions MUST verify compliance with these principles.

**Amendment Process**: Constitutional changes require explicit documentation of the modification rationale and team consensus.

**Compliance Review**: Regular audits MUST verify adherence to UV management, KISS principle implementation, and change communication standards.

**Version**: 1.0.0 | **Ratified**: 2025-09-27 | **Last Amended**: 2025-09-27