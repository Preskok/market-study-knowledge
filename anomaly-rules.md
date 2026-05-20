# Anomaly Detection Rules

These rules are applied during `ams-health` runs after reading the Baselines section of the history canvas.

## Prerequisites

- Skip ALL anomaly detection if `total_runs < 14`. Print: `⏳ Learning... (N/14 runs before anomaly detection)`
- Load: current run's queue states, current hour (`date +%H` → integer), current timestamp

## Rule 1: Drain anomaly (1.5h+ late)

For each queue where `baselines.queues[name].typical_drain_hour` is defined:

```
typical_drain_hour = baselines.queues[name].typical_drain_hour   # float, e.g. 9.5
pct_zero_at_drain  = baselines.queues[name].by_hour[floor(typical_drain_hour)].pct_zero
current_messages   = current run queue messages
current_hour       = integer hour

FIRE when:
  pct_zero_at_drain >= 0.80          # queue is usually empty at this hour
  AND current_messages > 0            # but it's not empty now
  AND (current_hour - typical_drain_hour) >= 1.5   # and we're 1.5h+ past typical drain
```

Alert text: `⚠️ **MS_X** usually empty by HH:30, still N,NNN msgs — 1.5h+ late`

## Rule 2: Stuck queue

Read last 3 entries in Raw Data for this queue.

```
last3_messages = [entry.q[name][0] for entry in raw_data[-3:] if name in entry.q]

FIRE when:
  len(last3_messages) == 3
  AND all values equal
  AND last3_messages[0] > 0
```

Alert text: `⚠️ **MS_X** stuck at N msgs across last 3 runs (~Xh)`

Note: For stuck detection only, read the Raw Data section (not just Baselines). Limit to last 3 entries.

## Rule 3: Consumer drop

```
baseline_consumers = baselines.queues[name].baseline_consumers   # float
current_consumers  = current run queue consumers

FIRE when:
  baseline_consumers > 0
  AND current_consumers < baseline_consumers * 0.5
```

Alert text: `⚠️ **MS_X** only N consumers (baseline: B)`

## Rule 4: DL incident trend

```
dl_incidents_7d = baselines.dl_incidents_7d[queue_name]   # integer

FIRE when:
  dl_incidents_7d >= 2
```

Alert text: `⚠️ **MS_DL** had N incidents in last 7 days — recurring issue`

## Rule 5: 30-day record high

```
max_30d           = baselines.queues[name].max_30d   # integer
current_messages  = current run queue messages

FIRE when:
  current_messages > max_30d
  AND current_messages > 1000
```

Alert text: `📈 **MS_X** at N,NNN msgs — new 30-day record (prev max: M,MMM)`

## Output format

Print before Verdict section:

```
## ⚠️ Anomaly Alerts

- ⚠️ MS_GENERAL_LISTING_URLS_TO_FETCH: usually empty by 09:30, still 4,200 msgs — 1.5h+ late
- ⚠️ MS_DL: had 3 incidents in last 7 days — recurring issue
```

If no anomalies and total_runs >= 14: print nothing (don't add the section at all).
