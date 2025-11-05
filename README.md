# autobook
a Dockerized web app that automates audiobook organization end-to-end.

# AutoBook
The ultimate, automated audiobook organizer that makes others obsolete. Dockerized web app for messy-to-clean conversion.

## Features
- Auto-group flat files, multi-source metadata (Audible, Google Books, OpenLibrary, beets).
- M4B conversion with chapters/covers.
- Real-time UI progress, uploads, logs.
- Structured output for Audiobookshelf.

## Installation
1. `docker-compose up -d`
2. Access http://localhost:8000
3. Mount /input and /output as needed.
4. Optional env: ABS_URL and ABS_API_KEY for Audiobookshelf integration.

Run `python manage.py migrate` first time.
