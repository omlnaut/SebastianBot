---
agent: agent
---
Compare the code changes between the current git branch and the given branch. if none is give, use 'main'. Check if the code changes adhere to the instruction files listed in .github/instructions (md, nested)
Check if any instructions were violated. If so, fix the violations. Also check the code changes to spot any patterns that are not yet part of the instructions, if so, add to the respective instructions file.
Also check the chat history for any new requirements that are not yet part of the instructions, if so, add to the respective instructions file.

Make sure to only suggest changes that are relevant to the instructions and avoid unnecessary modifications. Also make sure that the changes go to the right instruction files.