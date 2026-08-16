# Data Retention Policy

## Scope

This policy applies to all event data, logs, and analytics records produced
by services in the platform. It does not cover customer PII, which is
governed by the separate privacy policy.

## Retention periods

Raw event data is retained for 90 days in hot storage, then archived to cold
storage for 2 years. Aggregated analytics tables are retained indefinitely.
Debug logs are retained for 30 days.

## Deletion requests

Deletion requests must be filed through the governance queue and are
processed within 30 days. Emergency deletions require director approval.
