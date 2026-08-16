# Deployment and Rollback Runbook

## Standard deployment

Deployments go through the staged pipeline: canary (5% traffic, 30 minutes),
then 50%, then full rollout. Error-rate and latency dashboards must stay
within thresholds at each stage.

## Rollback procedure

If the canary breaches error thresholds, the pipeline auto-rolls back. Manual
rollback is one command: promote the previous known-good build. Never roll
forward during an active incident without incident commander sign-off.
