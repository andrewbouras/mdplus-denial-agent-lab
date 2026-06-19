# Security and data handling

This repository is an internal research prototype, not a production patient
application.

- Use synthetic or fully de-identified inputs only.
- Do not commit denial letters, insurance cards, patient details, episode
  folders, policy-library documents, controller keys, or credentials.
- Episode output is stored under `outputs/` by default and is gitignored.
- The web agent relies on a macOS `sandbox-exec` read barrier to prevent access
  to the internal policy library and sibling agent workspace.
- Review the generated work order, sandbox profile, and selected source before
  relying on any result.
- The system does not provide medical or legal advice and does not guarantee
  insurance coverage or appeal success.

If this prototype is adapted for real patient data, add authentication,
authorization, encrypted storage and transport, retention/deletion controls,
audit review, abuse protections, and an appropriate HIPAA/privacy assessment
before deployment.
