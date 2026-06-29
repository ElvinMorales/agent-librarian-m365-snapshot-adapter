# Approved-scope configuration

`examples/approved-scope.example.json` is public-safe and fabricated. It defines:

- a placeholder source system and locator
- exactly one approved library/folder root
- exclusions, allowed extensions, and maximum traversal depth
- approval owner and timestamp
- sensitivity and inherited output handling

`check-config` fails closed when a required field is absent, the included root is
broad or ambiguous, a path contains traversal, an extension is outside the
adapter's fixed allowlist, or sensitivity inheritance is disabled.

The prototype deliberately requires a folder below a library: a single segment
such as `Shared Documents`, `/`, `root`, `all`, or a wildcard is not accepted.
Configuration validation must occur before any future remote access.

Do not edit the public example with real values. Put local configuration outside
the repository and keep it out of source control. Real source locators and file
names can disclose organizational structure even when they are not auth data.
