# Anomaly Detection Rules

These rules are applied during `ams-health` runs after reading the Baselines section of the history canvas.

## Slot definition

Every run belongs to one of two slots based on the timestamp hour (UTC, as stored in Raw Data):

| Slot | Hour range | Scheduled time |
|------|-----------|----------------|
| `0700` | hour < 8 | 07:00 CEST daily |
| `1000` | hour >= 8 | 10:00 CEST daily |

**Always compare a run against its own slot's baselines only.**  
`current_slot = "0700" if current_hour < 8 else "1000"`  
`slot_baselines = baselines.slots[current_slot]`

## Prerequisites

- Skip ALL anomaly detection if `slot_baselines.total_runs < 14`. Print: `⏳ Learning... (N/14 runs for SLOT slot before anomaly detection)`
- Load: current run's queue states, current hour (`date +%H` → integer), current timestamp

## Baselines schema (canvas Baselines section)

```json
{
  "updated": "2026-05-27T06:12+00:00",
  "total_runs": 19,
  "slots": {
    "0700": {
      "total_runs": 10,
      "queues": {
        "MS_EXAMPLE": {
          "max_30d": 99234,
          "baseline_consumers": 4.0,
          "pct_zero": 0.3,
          "typical_drain_hour": 7
        }
      },
      "dl_incidents_7d": { "MS_DL": 3 }
    },
    "1000": {
      "total_runs": 9,
      "queues": { "...": {} },
      "dl_incidents_7d": { "MS_DL": 5 }
    }
  }
}
```

## Baseline computation (used by `ams-health sync` and the dedup script)

1. Parse all JSONL lines from Raw Data section of the canvas.
2. Deduplicate: for each (date, slot), keep only the **last** entry by timestamp.
   - slot = `"0700"` if hour < 8, else `"1000"`
3. Split deduplicated entries by slot. Compute per slot:
   - `total_runs`: count of unique (date, slot) entries
   - Per queue: `max_30d` (max messages in last 30 days), `baseline_consumers` (avg consumers), `pct_zero` (fraction of runs where messages=0), `typical_drain_hour` (hour with pct_zero >= 0.6 and count >= 2, highest pct_zero wins)
   - `dl_incidents_7d`: count of runs in last 7 days where DL queue had messages > 0

## Rule 1: Drain anomaly (1.5h+ late)

Uses **slot-specific** baselines.

```
typical_drain_hour = slot_baselines.queues[name].typical_drain_hour   # integer hour
pct_zero           = slot_baselines.queues[name].pct_zero
current_messages   = current run queue messages
current_hour       = integer hour

FIRE when:
  typical_drain_hour is defined
  AND pct_zero >= 0.80
  AND current_messages > 0
  AND (current_hour - typical_drain_hour) >= 1.5
```

Alert text: `⚠️ **MS_X** usually empty by HH:30 (at this time), still N,NNN msgs — 1.5h+ late`

## Rule 2: Stuck queue

Read last 3 entries **of the same slot** from Raw Data for this queue.

```
same_slot_entries = [e for e in raw_data if slot(e) == current_slot]
last3 = same_slot_entries[-3:]
last3_messages = [e.q[name][0] for e in last3 if name in e.q]

FIRE when:
  len(last3_messages) == 3
  AND all values equal
  AND last3_messages[0] > 0
```

Alert text: `⚠️ **MS_X** stuck at N msgs across last 3 SLOT runs (~3 days)`

## Rule 3: Consumer drop

Uses **slot-specific** baselines.

```
baseline_consumers = slot_baselines.queues[name].baseline_consumers
current_consumers  = current run queue consumers

FIRE when:
  baseline_consumers > 0
  AND current_consumers < baseline_consumers * 0.5
```

Alert text: `⚠️ **MS_X** only N consumers (baseline: B)`

## Rule 4: DL incident trend

Uses **slot-specific** dl_incidents_7d.

```
dl_incidents_7d = slot_baselines.dl_incidents_7d[queue_name]

FIRE when:
  dl_incidents_7d >= 2
```

Alert text: `⚠️ **MS_DL** had N incidents in last 7 days — recurring issue`

## Rule 5: 30-day record high

Uses **slot-specific** baselines.

```
max_30d          = slot_baselines.queues[name].max_30d
current_messages = current run queue messages

FIRE when:
  current_messages > max_30d
  AND current_messages > 1000
```

Alert text: `📈 **MS_X** at N,NNN msgs — new 30-day record for SLOT slot (prev max: M,MMM)`

## Output format

Print before Verdict section:

```
## ⚠️ Anomaly Alerts

- ⚠️ MS_GENERAL_LISTING_URLS_TO_FETCH: usually empty by 09:30 (at this time), still 4,200 msgs — 1.5h+ late
- ⚠️ MS_DL: had 3 incidents in last 7 days — recurring issue
```

If no anomalies and slot total_runs >= 14: print nothing (don't add the section at all).
