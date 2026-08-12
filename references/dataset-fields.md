# Research Dataset Products

## data_collection.csv

One row equals one anonymized run. The row contains:

- consent and anonymous run identifiers;
- M scan metadata and data-quality coverage;
- all W scoring metrics, including missing/degraded state;
- all G zero-weight research candidates;
- four-axis scores, confidence, coverage, and metric contributions;
- raw/display work type and scorer version;
- beta labels and 1-7 ratings after feedback is collected.

This is the table to merge across 48-80 participants. The campaign owner should append rows by matching column names, then analyze axis-level accuracy and feature usefulness.

## evidence_table.csv

A long-format audit table. One row equals one W or G field. Use it to inspect why an individual result was produced and whether a field was missing, degraded, or overrepresented.

## Privacy

Neither table stores source text, filenames, paths, names, contact details, or detected entities. `research_consent=no` means the files remain local and must not be submitted or uploaded.
