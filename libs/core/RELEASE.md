# Release Notes

## 0.3.0
- Rulebook ingestion (`games_rule_core.ai.ingest`): Gemini extracts structured rules from the PDF, pages are chunked and embedded into pgvector, and a cover is either rendered from page 1 or generated.
- ADK rules judge agent (`games_rule_core.ai.agent`) with rulebook search and game overview tools.
- `Game` model reshaped for ingestion (status, structured JSONB rules, cover path); `Rulebook` renamed to `GameDocument` with a `file_path`.
- SQL echo turned off.

## 0.2.0
- restructured porject

## 0.1.7
- fixed model (more)

## 0.1.6
- fixed model

## 0.1.5
- removed extra in sqlmodel

## 0.1.4
- use env variables for login details

## 0.1.3
- added relationships

## 0.1.2
- added relationships

## 0.1.1
- fix package name

## 0.1.0
- Initial release of package
