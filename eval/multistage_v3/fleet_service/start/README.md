# fleetkeep

Maintenance records for a company's vehicle fleet: odometer and fuel logs,
service intervals by distance and time, work orders with parts and labour,
downtime, and cost-per-mile reports.

```
fleetkeep --fleet north init --name "North depot"
fleetkeep --fleet north vehicle add VAN-101 --class light --make Ford --model Transit --year 2025 --in-service 2025-09-01
fleetkeep --fleet north odometer add VAN-101 5900
fleetkeep --fleet north due
```

Settings, file formats, report columns and error codes are listed in
`docs/reference.md`. Run the tests with `python -m pytest`.
