---
name: new_client_feature
description: describes how to create new features for external interaction (i.e. new client methods)
---

# New Client Feature Development Guide
Always start with a jupyter notebook in the clients folder to quickly iterate on the new client feature.
If available, use the existing client where possible, i.e. by accessing the underlying client session and reusing existing methods.


Once the feature is working in the notebook, notify the user and wait for approval. Move the code to the respective client file, add integration tests (only ever invoked by the user, never the agent) and cleanup the notebook (removing the 'manual' investigation and use the new client method to demonstrate the feature).
