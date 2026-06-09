# Agent Instructions

These instructions apply to all work in this repository.

## Source Of Truth

- Use existing schemas, enums, constants, and typed APIs as the source of truth.
- Before adding business logic around categories, effects, statuses, filters, or identifiers, find the existing definition in the codebase or the official API documentation.
- Do not invent aliases, synonym maps, spelling corrections, or value normalization for domain values unless an existing schema/utility already defines that behavior or the user explicitly asks for it.

## No Hidden Domain Expansion

- Do not broaden requested behavior by mapping nearby values together. For example, do not treat `LIMITED` as `RESTRICTED`, `MODIFIED` as `RESTRICTED`, or `UNAVAILABLE` as `UNSERVICEABLE` unless that mapping is already part of the relevant data contract.
- If a feature asks for exact enum values, compare exact enum values.
- Unknown, malformed, legacy, or unexpected values should fall through to the default behavior unless there is a documented compatibility requirement.

## No Undocumented Fallbacks

- Do not add or rely on fallback data sources, fallback API calls, fallback mappings, fallback defaults, or fallback UI behavior unless an existing schema, utility, data contract, or explicit user request defines that fallback.
- If the authoritative source is missing, unavailable, or ambiguous, fail visibly or stop and verify instead of silently substituting another value, source, or behavior.

## Avoid Fragile String Logic

- Avoid regex lookups, substring matching, or ad hoc string parsing for structured domain fields when typed fields, enums, or parsed data are available.
- Use regex only when the input is genuinely unstructured text and there is no better structured representation.
- When regex or string normalization is necessary, keep it local, explain why it is necessary, and cover it with focused tests.

## Hardcoding

- Do not hardcode domain lists or priority tables if a canonical constant, enum, schema, or API-provided list exists.
- If a new hardcoded ordering is required by product behavior, keep it in one named constant, make the ordering explicit, and add tests for it.

## Verification Commands

- Do not run `npm run build` or `next build` as post-development test or validation commands.
- Use targeted tests, type checks, linters, or narrower verification commands that match the repository docs. If no appropriate verification command is known, state that verification was not run instead of substituting a production build.

## When Unsure

- Stop and verify the source of truth instead of guessing.
- If the codebase has conflicting conventions, follow the convention closest to the feature being changed and call out the conflict.
