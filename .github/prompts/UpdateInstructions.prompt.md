---
agent: agent
---
Compare the code changes between the current git branch and the given branch. if none is give, use 'main'. Check if the code changes adhere to the instruction files listed in .github/instructions (md, nested)
Check if any instructions were violated. If so, fix the violations. Also check the code changes to spot any patterns that are not yet part of the instructions, if so, add to the respective instructions file.
Also check the chat history for any new requirements that are not yet part of the instructions, if so, add to the respective instructions file.

Additionally, check if changes affect project documentation (README.md) or any of the notes in notes/dev_setup. If the code changes introduce new features, automations, or architectural changes that should be reflected in the README, update it accordingly.

Make sure to only suggest changes that are relevant to the instructions and avoid unnecessary modifications. Also make sure that the changes go to the right instruction files.

If you encounter code that seems like it could be refactored for better readability, maintainability, or performance, suggest those refactors as well. Check for code in the codebase that is tagged with the comment #WaitForRefactor.
#WaitForRefactor is used to mark code that needs refactoring, but so far is only used in a single place. If you find new code that matches the use case, it's worth refactoring.
Example are are the tests in "test_azure_functions.py" that parse azure functions to check for the presence of certain functions. If you find similar code in other test files, refactor it into a common utility function and update the instruction files accordingly.