# API Versioning Policy

## Breaking changes

A breaking change is any change that removes a field, renames a field,
changes a field type, or changes the semantics of an existing endpoint.
Breaking changes require a new major version and a 6-month deprecation
window for the old version.

## Deprecation process

Deprecated endpoints must emit a deprecation header, be documented in the
changelog, and have all internal callers migrated before shutdown.

## Sunset criteria

An old version can be shut down when traffic drops below 0.1% of total for
30 consecutive days and all known internal callers have migrated.
