# Operational Rules

## 1. UI/UX Design (Non-Negotiable)
- **Theme**: Mandatory Dark Theme. Base background color: `#0f172a`.
- **Navigation**: Unified Top Navigation items (Dashboard | Search | Magazine) must be present in `layout.html`.
- **Flow**: Do NOT create "Go Back" buttons. Use navigation breadcrumbs or main nav only.
- **Typography**: Optimized for bilingual readability (e.g., Inter for EN, Amiri/Traditional Arabic for AR).

## 2. Graphic & File Handling
- **Uploads**: ALWAYS use `FormData` object for sending files/images from browser to Flask.
- **Payloads**: Do NOT use JSON payloads for file uploads.
- **Placeholders**: UI must gracefully handle missing images with polished placeholders.

## 3. Code & Security
- **Secrets**: NEVER hardcode API keys or secrets. Always use `.env` and `os.environ`.
- **Bilingual Layouts**: Text must be displayed side-by-side: English (Left) -> Arabic (Right).
- **Modularity**: Skills must remain CLI-testable and independent of the Flask request context.

## 4. Stability
- **Filesystem**: Do not rename files or alter the folder structure once established.
- **Dependencies**: Keep `requirements.txt` minimal and clean.
