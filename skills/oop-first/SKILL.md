---
name: oop-first
description: >-
  Applies object-oriented-first architecture to improve encapsulation,
  cohesion, maintainability, and AI collaboration. Use when designing,
  implementing, modifying, extending, refactoring, or reviewing code
  in any programming language.
---

# OOP First

Prefer object-oriented architecture when organizing related functionality.
Optimize for clear ownership, encapsulation, stable interfaces, and localized changes.

## Core Rules

1. **Object-first organization**
   - Prefer cohesive classes, objects, or equivalent language constructs over scattered standalone functions.
   - Keep related data, state, and behavior together.
   - Give each component a clear responsibility and reason to change.

2. **Encapsulation**
   - Keep implementation details and mutable state internal.
   - Expose small, intentional, stable public interfaces.
   - Enforce invariants through the component that owns them.
   - Avoid external code directly manipulating another component's internals.

3. **Cohesion and coupling**
   - Group functionality by responsibility, not merely by operation type.
   - Prefer composition and explicit dependencies over unnecessary inheritance or hidden coupling.
   - Avoid circular dependencies, duplicated responsibilities, and shared mutable global state.
   - Keep changes localized to the components that own the affected behavior.

4. **Internal structure**
   - Separate public operations, internal implementation, and workflow coordination when it improves clarity.
   - Split complex methods into meaningful internal operations.
   - Avoid god classes, excessive delegation, deep call chains, and fragmented abstractions.

5. **Pragmatic abstraction**
   - Use standalone functions for pure calculations, stateless transformations, and simple utilities when appropriate.
   - Respect each language's idiomatic mechanisms for encapsulation and composition.
   - Do not force classical OOP patterns onto languages where other constructs are more natural.
   - Prefer the simplest design that preserves clear responsibilities and future extensibility.

## Coding Workflow

### New code

- Identify responsibilities, state ownership, and component boundaries before implementation.
- Define necessary public interfaces before internal details.
- Place new behavior in the component that should own it.
- Avoid speculative abstractions for hypothetical future requirements.

### Modifications

- Inspect existing ownership, interfaces, callers, and tests.
- Extend the responsible component instead of creating parallel implementations.
- Preserve established contracts and behavior unless changes are explicitly required.
- Avoid unrelated refactoring or unnecessary structural changes.

### Refactoring

- Target concrete problems in cohesion, encapsulation, coupling, or change isolation.
- Improve boundaries without introducing unnecessary layers.
- Preserve observable behavior and verify affected interfaces.

### Code review

- Evaluate responsibility placement, state ownership, interface clarity, and change impact.
- Identify concrete maintainability problems rather than stylistic preferences alone.
- Recommend the smallest meaningful architectural improvement.

## AI Collaboration

- Make component responsibilities and public contracts discoverable from the code.
- Keep internal details behind stable interfaces to support independent implementation and testing.
- Prefer changes that another agent can understand, verify, and extend without reconstructing unrelated parts of the system.
- Test behavior through public contracts where practical; test pure functions directly.
- Explain significant architectural decisions only when they are non-obvious or affect future work.

## Boundaries

- OOP is a default preference.
- Explicit requirements and established project architecture take precedence.
- Do not optimize for class count, method count, file count, or lines of code.
- Do not introduce patterns, abstractions, or boilerplate solely to satisfy this skill.
- Apply these principles during normal coding without requiring lengthy architectural explanations.
