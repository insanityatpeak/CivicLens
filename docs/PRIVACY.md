# Privacy

What CivicLens does with your data, as implemented in this repository.

## Processed
- **Your photo.** Validated, auto-rotated, resized (longest side 1568 px) and re-encoded as JPEG, which drops EXIF metadata including GPS. The re-encoded image is sent to the configured AI provider (Groq, OpenRouter or Google Gemini, tried in that order) for analysis.
- **Text you type** (location, notes, answer to the clarifying question) and the evidence list derived from your photo. These are sent to an AI provider to write the draft.
- **Your IP address**, held in server memory only, to enforce the 10-analyses-per-hour limit. It is not written to disk or logs.

## Not stored
- Photos, drafts and typed text are not saved by the app. There is no database and no account system.
- Server logs are JSON lines with request ID, method, path, status, latency, model name and issue category. They never contain photos or user-typed text.
- Nothing is submitted to any authority. You copy or download the draft and send it yourself.

## Third parties
Each AI provider receives the data above under its own terms and retention policy. Free-tier plans may use submitted data differently from paid plans; check the provider's current terms before uploading anything sensitive. Do not upload photos in which people are identifiable if you are not comfortable with that. The app warns when faces or number plates appear to be visible.

## Retention
The app keeps no data beyond the lifetime of a request, except the in-memory rate-limit counter, which is cleared on restart. Hosting-platform request logs (for example Render's) are outside this app's control.
