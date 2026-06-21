# Greek PII Public Benchmark v1 — 3-Way Model Comparison

Benchmark: `/workspace/benchmarks/greek_pii_public_v1/cases.jsonl`

## Aggregate Metrics

| Model | Cases | Gold spans | Pred spans | Untyped P | Untyped R | **Untyped F1** | Typed P | Typed R | **Typed F1** | Time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `opf_base` | 100 | 700 | 495 | 0.952 | 0.673 | **0.788** | 0.444 | 0.314 | **0.368** | 158.6 |
| `v2_13` | 100 | 700 | 580 | 0.962 | 0.797 | **0.872** | 0.862 | 0.714 | **0.781** | 150.3 |
| `v3_lite` | 100 | 700 | 462 | 0.974 | 0.643 | **0.775** | 0.866 | 0.571 | **0.688** | 170.3 |

## Per-Class Typed F1

| Class | `opf_base` F1 | `v2_13` F1 | `v3_lite` F1 |
|---|---:|---:|---:|
| `account_number` | 0.068 | 0.140 | 0.182 |
| `adt` | 0.000 | 0.833 | 0.400 |
| `afm` | 0.000 | 0.922 | 0.736 |
| `ama` | 0.000 | 0.667 | 0.364 |
| `amka` | 0.000 | 0.921 | 0.545 |
| `card_pan` | 0.000 | 0.824 | 0.571 |
| `cvv` | 0.000 | 0.500 | 0.500 |
| `driver_license` | 0.000 | 0.800 | 0.375 |
| `gemi` | 0.000 | 0.857 | 0.400 |
| `iban_gr` | 0.000 | 0.884 | 0.837 |
| `imei` | 0.000 | 0.800 | 0.500 |
| `ip_address` | 0.000 | 0.933 | 1.000 |
| `license_plate` | 0.000 | 0.500 | 0.455 |
| `mac_address` | 0.000 | 0.769 | 0.667 |
| `passport` | 0.000 | 0.250 | 0.286 |
| `pcn` | 0.000 | 0.909 | 0.500 |
| `private_address` | 0.377 | 0.943 | 0.870 |
| `private_date` | 0.833 | 0.920 | 0.914 |
| `private_email` | 0.961 | 0.953 | 0.865 |
| `private_person` | 0.368 | 0.735 | 0.602 |
| `private_phone` | 0.319 | 0.433 | 0.617 |
| `private_url` | 0.240 | 0.300 | 0.500 |
| `secret` | 0.727 | 0.560 | 0.667 |
| `vehicle_vin` | 0.000 | 0.857 | 0.880 |

## Error Breakdown

| Model | Boundary | Confusion | Missed | Hallucinated |
|---|---:|---:|---:|---:|
| `opf_base` | 33 | 218 | 229 | 24 |
| `v2_13` | 13 | 45 | 142 | 22 |
| `v3_lite` | 16 | 34 | 250 | 12 |
