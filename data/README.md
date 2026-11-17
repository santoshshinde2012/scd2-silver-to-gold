# Synthetic history data

[`history.json`](history.json) contains the complete seed for the local Silver-to-Gold example. All customer records, adviser assignments, and events are synthetic; the city names refer to real places.

## Fields

| Key | Contents |
| --- | --- |
| `note` | Descriptive metadata; the loader does not use it. |
| `silver_first_load` | Initial open customer spans for customers 42 and 7. |
| `move_42` | Customer 42 moves from Pune to Mumbai on 1 June 2026. |
| `move_7` | Customer 7 moves from Delhi to Jaipur on 1 September 2026. |
| `correction_42` | A later correction changes customer 42's move date to 20 May 2026. |
| `advisers_42` | Customer 42's adviser periods, changing from Santosh to Ravi on 15 March 2026. |

Customer rows contain `customer_id`, `city`, `valid_from`, and `valid_to`. Adviser rows use `adviser` in place of `city`. Move and correction objects contain `customer_id`, `city`, and `on`.

Dates are ISO `YYYY-MM-DD` strings describing business validity. Periods include their start and exclude their end: `[valid_from, valid_to)`. A `null` end denotes an open span. Adjacent spans therefore do not overlap.

## Scenario order

1. Load the two initial customer spans.
2. Apply customer 42's move, then demonstrate the copy-and-replay failure.
3. Bootstrap the separate Gold copy at Silver version 2.
4. Apply customer 7's move and catch Gold up from the recorded version.
5. Correct customer 42's move date and compare delete-ignoring and delete-aware policies.
6. Read the latest Silver through the view wrapper.
7. Join customer 42's **pre-correction** city history to the adviser periods.

The temporal join intentionally retains the original 1 June city boundary, while the correction results use 20 May. Commit order and business-date order are separate concepts.

The loader expects this fixed shape and does not validate arbitrary input. The correction helper is tailored to this customer's two-span history; changing the seed to contain multiple moves requires changing that logic as well.

See the [project README](../README.md) for execution instructions, the SOLID assessment, and implementation limits.
