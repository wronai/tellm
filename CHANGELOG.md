# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.10] - 2026-06-14

### Fixed
- Fix relative-imports issues (ticket-9d339d03)
- Fix relative-imports issues (ticket-8878cd9a)
- Fix string-concat issues (ticket-6b812730)
- Fix relative-imports issues (ticket-4c4369af)
- Fix string-concat issues (ticket-19757ea1)

## [0.1.10] - 2026-06-14

### Fixed
- Fix relative-imports issues (ticket-920d651c)
- Fix smart-return-type issues (ticket-26f50f26)
- Fix unused-imports issues (ticket-78f9b30f)
- Fix magic-numbers issues (ticket-9ef11828)
- Fix relative-imports issues (ticket-1c7db970)
- Fix smart-return-type issues (ticket-6d603cca)
- Fix ai-boilerplate issues (ticket-ef74b6ca)
- Fix relative-imports issues (ticket-c9fdf3eb)
- Fix string-concat issues (ticket-fc4cbc1e)
- Fix relative-imports issues (ticket-04b93bfd)
- Fix relative-imports issues (ticket-85bde04e)
- Fix string-concat issues (ticket-8e59420c)
- Fix smart-return-type issues (ticket-01f1a91e)
- Fix magic-numbers issues (ticket-f7199ff5)
- Fix string-concat issues (ticket-742e2d66)

## [0.1.10] - 2026-06-14

### Fixed
- Fix relative-imports issues (ticket-21179bdb)
- Fix smart-return-type issues (ticket-fd28744f)
- Fix unused-imports issues (ticket-7892c43b)
- Fix magic-numbers issues (ticket-f2a66b43)
- Fix relative-imports issues (ticket-7a82e4a6)
- Fix smart-return-type issues (ticket-6d6bc20b)
- Fix unused-imports issues (ticket-24a95ab4)
- Fix magic-numbers issues (ticket-6511e0b7)
- Fix smart-return-type issues (ticket-0536866c)
- Fix ai-boilerplate issues (ticket-e24d192a)
- Fix relative-imports issues (ticket-8cc3c499)
- Fix smart-return-type issues (ticket-a88e27f2)
- Fix string-concat issues (ticket-b42a836a)
- Fix magic-numbers issues (ticket-e1aa27ed)
- Fix relative-imports issues (ticket-47889804)
- Fix smart-return-type issues (ticket-2d50e46e)
- Fix string-concat issues (ticket-35e9bf44)
- Fix magic-numbers issues (ticket-c8620ed3)
- Fix relative-imports issues (ticket-8a485558)
- Fix smart-return-type issues (ticket-93a398fe)
- Fix string-concat issues (ticket-e2694c99)
- Fix magic-numbers issues (ticket-d54afc1f)
- Fix smart-return-type issues (ticket-6ebb860f)
- Fix ai-boilerplate issues (ticket-09e26591)
- Fix string-concat issues (ticket-c3b8cc69)
- Fix unused-imports issues (ticket-1e6506f5)
- Fix ai-boilerplate issues (ticket-67616696)
- Fix relative-imports issues (ticket-7e46915d)
- Fix smart-return-type issues (ticket-6e14f63f)
- Fix string-concat issues (ticket-c1d0f305)
- Fix magic-numbers issues (ticket-860ab996)
- Fix string-concat issues (ticket-3ab1d4ef)
- Fix unused-imports issues (ticket-c1041eb7)
- Fix magic-numbers issues (ticket-f2cabeb5)
- Fix ai-boilerplate issues (ticket-79277ab6)
- Fix smart-return-type issues (ticket-001d67d8)
- Fix string-concat issues (ticket-928fbc67)
- Fix llm-hallucinations issues (ticket-af40c0e5)

## [Unreleased]

### Docs
- Add project documentation under `docs/` with getting started, architecture, API/protocols, registry URI, workflow/autoimprovement and testing guides.
- Link `docs/` from README and TODO.

### Fixed
- Handle LLM responses where `message.content` is empty but JSON is available in reasoning/provider-specific fields.
- Reject country-level weather locations such as `Polska` with a structured `LOCATION_TOO_BROAD` service error instead of geocoding an arbitrary country point.
- Treat schema-valid registry service errors as locally valid workflow outcomes, avoiding unnecessary LLM validation waits.
- Route product price questions to `tellm://service/price/search` instead of `domain.check` or generated `run` functions.

### Added
- Add browser UI action for copying workflow logs to the clipboard.
- Add workflow timing diagnostics for router, execution, rendering, LLM validation and total duration.
- Add Open-Meteo geocoding/forecast timing diagnostics to `weather.current` results.
- Route simple weather queries locally to `tellm://service/weather/current` without an LLM router call.
- Confirm trusted schema-valid registry results with local validation instead of calling LLM validation.
- Add `tellm://service/price/search` for supported commerce price lookup with structured errors such as `PRICE_NOT_FOUND`.

### Tests
- Add regression coverage for parsing JSON from reasoning-only LLM responses.

## [4.0.6] - 2026-06-14

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/README.md
- Update docs/api.md
- Update docs/architecture.md
- Update docs/getting-started.md
- Update docs/registry-and-uri.md
- ... and 4 more files

### Test
- Update tests/test_tellm.py

### Other
- Update MANIFEST.in
- Update app.doql.less
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- ... and 16 more files

## [4.0.5] - 2026-06-14

### Docs
- Update README.md

### Test
- Update tests/test_tellm.py

### Other
- Update project/planfile-tickets.yaml
- Update tellm/__init__.py
- Update tellm/bot.py
- Update tellm/improvement/runner.py
- Update tellm/registry/core.py
- Update tellm/server.py

## [4.0.4] - 2026-06-14

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql-scenarios/generated-from-pytests.testql.toon.yaml
- Update tests/test_tellm.py

### Other
- Update .gitignore
- Update app.doql.less
- Update bot.py
- Update planfile.yaml
- Update prefact.yaml
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- ... and 28 more files

## [4.0.3] - 2026-06-14

### Docs
- Update README.md

## [4.0.2] - 2026-06-14

### Docs
- Update README.md

### Test
- Update tests/test_tellm.py

### Other
- Update .gitignore
- Update MANIFEST.in
- Update __init__.py
- Update output/tellm-4.0.2-py3-none-any.whl
- Update output/tellm-4.0.2.tar.gz
- Update server.py

## [4.0.1] - 2026-06-14

### Docs
- Update README.md

### Test
- Update tests/test_tellm.py

### Other
- Update .env.example
- Update .gitignore
- Update __init__.py
- Update bot.py
- Update config.py
- Update main.py
- Update requirements.txt
- Update server.py
