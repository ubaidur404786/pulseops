# Gateway runbook

## Checks
- Check the request rate for a traffic spike or a bot.
- Check TLS and routing errors in the gateway logs.
- Check if a config change went out recently.

## Action
Roll back the latest gateway config and enable rate limiting.
