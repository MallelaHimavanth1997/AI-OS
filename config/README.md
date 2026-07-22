# Configuration

The configuration layer owns all environment-driven settings for AI-OS. Secrets must remain in `.env` or the runtime environment, and application code should read settings through typed configuration objects rather than hardcoded constants.

## Expected Responsibilities

- App-wide settings and feature flags.
- Database connection settings.
- LLM and Ollama settings.
- OAuth and API credentials.
- Working-hours and scheduler configuration.
