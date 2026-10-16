# Methodology

## Business problem

The project asks: **where should an operations team focus triage and staffing attention to reduce long-running NYC 311 requests?**

## Scope

The analysis uses requests created in Q1 2025. The official dataset is updated daily, so later source updates can change closed dates and therefore resolution times. The download script records the query so the extract can be reproduced.

## Resolution risk

A request is considered a 72-hour breach when it has a valid closed timestamp and took more than 72 hours from creation to closure. The 72-hour threshold is a transparent portfolio assumption used to compare operational risk; it is not claimed to be an official city SLA.

## Priority queue

Complaint-type priority is calculated as:

`request volume × breach rate × median resolution hours`

This intentionally balances workload, risk, and time-to-resolution. It is a prioritisation score rather than a causal estimate or a budget recommendation.

## Predictive model

A logistic-regression model is trained on January–February 2025 closed requests and evaluated on March 2025 closed requests. It uses only intake-time fields: agency, problem type, location type, borough, intake channel, day of week, hour, and weekend flag. The temporal split prevents March information from leaking into training.

## Limitations

The source contains administrative timestamps, not a controlled experiment. Long duration may reflect legitimate investigation complexity, data-entry conventions, or agency-specific workflow. The dataset does not include staffing levels, true service-level targets, customer severity, or cost. Recommendations should therefore be validated with agency operations teams before implementation.
