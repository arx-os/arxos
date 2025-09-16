# ArxOS Web Static Assets

This directory contains static assets for the HTMX web interface.

## Structure

- `css/` - Custom CSS files (if needed beyond Tailwind CDN)
- `js/` - Custom JavaScript files (minimal, HTMX-focused)
- `images/` - Images, icons, logos
- `fonts/` - Custom fonts (if needed beyond system fonts)

## Usage

Static files are served by the Go web server at `/static/` URLs.

Example:
- `web/static/css/custom.css` → `http://localhost:8080/static/css/custom.css`
- `web/static/images/logo.png` → `http://localhost:8080/static/images/logo.png`

## HTMX Philosophy

Following HTMX principles, this directory should contain minimal JavaScript:
- No complex frontend frameworks
- No build processes or bundling
- Simple, progressive enhancement only
