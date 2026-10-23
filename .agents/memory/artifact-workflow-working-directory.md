---
name: Artifact workflow working directory
description: Working-directory behavior for managed artifact preview workflows.
---

Managed artifact workflows start in the artifact's directory, not the workspace root. Write their commands relative to that directory (for example, `python app.py`) rather than changing into `artifacts/<slug>` again.

**Why:** A redundant `cd artifacts/<slug>` made the preview server fail because that path did not exist relative to the artifact directory.

**How to apply:** When editing a managed service command in `artifact.toml`, treat the artifact directory as the command's starting location.
