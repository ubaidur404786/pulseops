# Database runbook

## Checks
- Look at slow query log for queries over 1 second.
- Check open connections against the pool limit.
- Check disk and CPU on the database host.

## Action
Kill long-running queries and restart the connection pool.
