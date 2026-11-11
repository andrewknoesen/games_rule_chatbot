# Release Notes

## 0.3.1
- `GET /games/{id}/cover` sends the content type that matches the stored file.

## 0.3.0
- `POST /games/upload` takes a rulebook PDF and ingests it in the background.
- `POST /games/{id}/ask` answers rules questions with the ADK judge.
- `GET /games/{id}/cover` and `GET /games/{id}/rulebook` serve the stored files; `DELETE /games/{id}` removes a game and its files.
- Replaced the manual `POST /games/` and `/games/{id}/rulebooks` routes.
- Games left `processing` by a restart are marked `failed` at startup.

## 0.2.5
- imported new core package

## 0.2.4
- added exception handling

## 0.2.3
- Added postgres commands

## 0.2.2
- Added live and ready endpoints with sample code

## 0.2.1
- Added health check


## 0.2.0
- Added polyfactory

## 0.1.0
- Initial release of api package
