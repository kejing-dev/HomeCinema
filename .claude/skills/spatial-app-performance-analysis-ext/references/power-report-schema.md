# Power-Pressure Report Schema

The power mode analysis JSON should contain:

```json
{
  "schema_version": 2,
  "mode": "spatial_power_attribution_two_phase",
  "measurement": {
    "type": "trace_proxy",
    "direct_watts_available": false
  },
  "target": {
    "package": "target.client",
    "runtime_process": "com.pico.spatial.runtime"
  },
  "phases": {
    "baseline": {},
    "launched": {},
    "steady_state": {}
  },
  "collection": {
    "method": "capture_perf_data.py",
    "window_binding": "same_capture_window",
    "phase_alignment": "explicit_time_anchor"
  },
  "field_discovery": {
    "discovered_metrics": [],
    "missing_metrics": []
  },
  "runtime_metric_delta": {},
  "limitations": []
}
```

## Metric status

Each metric should preserve whether it is:

- `available`: both comparison values exist.
- `not_running`: the process or application was absent in that phase.
- `not_collected`: the collector did not provide the field.
- `not_comparable`: values exist but scope or phase alignment prevents a valid comparison.
- `not_reported`: analysis has the field but the report does not render it; this must fail generation.
- `new_value_from_zero`: baseline is zero; show the absolute new value without a percentage.

For a baseline value of zero:

- Do not emit infinity.
- Use `new_value_from_zero` and show the absolute delta.

## HTML contract

The HTML report must include:

1. Measurement mode and calibration limitation.
2. Phase definitions and exact input paths.
3. Client and shared Runtime identity.
4. Absolute values and relative change.
5. Color semantics: decrease green, increase red, unavailable/neutral gray.
6. Shared-service attribution caveat.
7. Recommended controlled A/B validation.
8. Field source, process ownership, sample count, and phase window for queried metrics.
9. Canonical output name: `spatial-power-attribution-report.html`.
10. Template path: `assets/power-report-template.html`.
