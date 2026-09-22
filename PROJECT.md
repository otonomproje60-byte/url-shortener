# URL Shortener Project

## Project Name
URL Shortener Service

## What it does
Provides a simple, self-hosted URL shortening service that converts long URLs into short, shareable links. Built with Python/Flask, SQLite, and Docker for easy deployment.

## Demo URL
http://77.90.53.243 (public VDS IP, accessible from external devices)

## Test Status
- Successfully shortens URLs (e.g., https://example.com -> http://localhost:5000/Mn8ktV, http://localhost:5000/svhBT2, http://localhost:5000/7wZIbf)
- Redirects correctly from short code to original URL
- Docker container builds and runs without errors
- All tests pass via test.sh

## Deployment Status
Deployed locally via Docker Compose. Service is accessible at http://localhost:5000 and has been stable for several hours.

## Known Limitations
- No user authentication or rate limiting (MVP)
- Analytics are optional and not yet implemented
- No custom domain support (requires reverse proxy configuration)
- Persistent storage uses SQLite; for high volume consider PostgreSQL or Redis

## Suggested Domain Names
(None yet - awaiting human purchase after validation)

## Next Steps
- Share MVP with developer communities (Reddit r/webdev, r/selfhosted, Hacker News, GitHub) to gather initial user feedback.
- Monitor usage and abuse potential.
- Consider adding basic rate limiting.
- Prepare domain recommendation for human review based on feedback.