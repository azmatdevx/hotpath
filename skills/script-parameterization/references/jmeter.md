# JMeter: parameterization

Verify names against the JMeter version in use.

## Data files
- **CSV Data Set Config**: set variable names, delimiter, and the file path (relative to the plan, resolvable on every generator). Choose:
  - **Sharing mode**: `All threads` (rows shared across the whole test), `Current thread group`, or `Current thread` (each thread reads the whole file).
  - **Recycle on EOF** and **Stop thread on EOF**: decide what happens when data runs out. For single-use data, recycle false and stop thread true, so you notice exhaustion.
  - **Ignore first line** when the file has a header.
- In distributed runs, each generator needs its own copy of the file. Split the file so generators do not reuse rows.

## Generated values
- `${__UUID()}`, `${__RandomString(...)}`, `${__Random(min,max)}`, `${__counter(TRUE,)}`, `${__threadNum}`, `${__time(...)}` for unique and time-based values. Combine `${__threadNum}` with a counter for per-user uniqueness.

## Setup and cleanup
- Use a **setUp Thread Group** to create data and a **tearDown Thread Group** to remove it. A **JDBC Request** can read or seed data.
- Use a **Random Variable** or a **JSR223** element for skewed or weighted choices.
