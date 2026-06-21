# Greek PII Public Benchmark v1 — 3-Way Model Comparison

Benchmark: `/workspace/benchmarks/greek_pii_public_v1/cases.jsonl`

## Aggregate Metrics

| Model | Cases | Gold spans | Pred spans | Untyped P | Untyped R | **Untyped F1** | Typed P | Typed R | **Typed F1** | Time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `opf_base` | 100 | 693 | 487 | 0.953 | 0.670 | **0.786** | 0.450 | 0.316 | **0.371** | 195.6 |
| `v2_13` | 100 | 693 | 570 | 0.961 | 0.791 | **0.868** | 0.867 | 0.713 | **0.782** | 171.8 |
| `v3_lite` | 100 | 693 | 452 | 0.980 | 0.639 | **0.774** | 0.872 | 0.569 | **0.688** | 143.4 |

## Per-Class Typed F1

| Class | `opf_base` F1 | `v2_13` F1 | `v3_lite` F1 |
|---|---:|---:|---:|
| `account_number` | 0.071 | 0.150 | 0.205 |
| `adt` | 0.000 | 0.861 | 0.400 |
| `afm` | 0.000 | 0.922 | 0.675 |
| `ama` | 0.000 | 0.667 | 0.364 |
| `amka` | 0.000 | 0.871 | 0.565 |
| `card_pan` | 0.000 | 0.824 | 0.667 |
| `cvv` | 0.000 | 0.500 | 0.667 |
| `driver_license` | 0.000 | 0.762 | 0.267 |
| `gemi` | 0.000 | 0.800 | 0.286 |
| `iban_gr` | 0.000 | 0.884 | 0.857 |
| `imei` | 0.000 | 0.800 | 0.500 |
| `ip_address` | 0.000 | 1.000 | 1.000 |
| `license_plate` | 0.000 | 0.500 | 0.522 |
| `mac_address` | 0.000 | 0.769 | 0.667 |
| `passport` | 0.000 | 0.000 | 0.286 |
| `pcn` | 0.000 | 0.667 | 0.000 |
| `private_address` | 0.353 | 0.932 | 0.839 |
| `private_date` | 0.815 | 0.933 | 0.908 |
| `private_email` | 0.954 | 0.953 | 0.857 |
| `private_person` | 0.379 | 0.744 | 0.629 |
| `private_phone` | 0.330 | 0.413 | 0.594 |
| `private_url` | 0.240 | 0.316 | 0.500 |
| `secret` | 0.727 | 0.560 | 0.667 |
| `vehicle_vin` | 0.000 | 0.857 | 0.880 |

## Error Breakdown

| Model | Boundary | Confusion | Missed | Hallucinated |
|---|---:|---:|---:|---:|
| `opf_base` | 34 | 211 | 229 | 23 |
| `v2_13` | 12 | 42 | 145 | 22 |
| `v3_lite` | 16 | 33 | 250 | 9 |
