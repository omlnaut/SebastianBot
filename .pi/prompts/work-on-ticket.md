---
description: Grab a refined ticket and start implementing
argument-hint: "<ticket-path>"
---

1. Read the ticket
2. Implement using TDD best practices
    - tests
        - for new features: write failing tests first, validate that they actually fail
        - for refactoring: verify that the code to be refactored is covered by tests
        - commit failing tests
    - implement
        - until tests are green

For python projects, use the python-lsp tools for navigation/linter checks

Ticket path: $@