# Inventory runbook

## Checks
- Check the stock sync job, it is the usual CPU hog.
- Check error logs for timeouts to the database.

## Action
Pause the stock sync job and scale inventory to 2 more replicas.
