# Identified Issues and Fixes

| Issue | Type | Line(s) | Description | Fix Approach |
|---|---|---|---|---|
| SQL Injection Vector (B608) | Security (Bandit) | 11 | String interpolation used in `INSERT` query (`'%s', %d, %d`), creating an injection vulnerability. | Replaced string interpolation with parameterized queries (`VALUES (?, ?, ?)`). |
| Insecure Deserialization via Pickle (B301, B403) | Security (Bandit) | 1, 43 | `pickle` imported and `pickle.loads(pickle.dumps(...))` used for snapshotting, posing arbitrary code execution risk. | Removed `pickle` module entirely; created clean shallow/deep copy using list comprehension `[tuple(row) for row in ...]`. |
| Hardcoded Sensitive Credential (B105) | Security (Bandit) | 6 | Plain-text password `NOC_PASSWORD = "tower-noc-77"` hardcoded into source code. | Extracted secret into environment variable via `os.getenv("NOC_PASSWORD", ...)` with safe default. |
| Broad Exception Clause (W0718) | Code Quality (Pylint) | 20 | Catching generic `Exception` masks unexpected errors and debugging signals. | Replaced with specific database exception `sqlite3.Error`. |
| Function Naming Convention (C0103) | Convention (Pylint) | 10, 15, 34 | CamelCase function names (`addTower`, `serviceTower`, `riskLevel`) violate PEP 8 convention. | Renamed functions to snake_case (`add_tower`, `service_tower`, `risk_level`). |
| Missing Documentation & Redundant Else (C0114, C0116, R1705) | Code Quality (Pylint) | 1, 10, 15, 25, 34, 38, 42, 46 | Missing module/function docstrings and unnecessary `else` block after `return`. | Added PEP 257 docstrings to module and functions; removed redundant `else` block. |
| Style & Formatting Violations (E501, E225, E303) | Style (Flake8) | 5, 11, 18, 25, 35, 43, 50 | Line length > 79 characters, excessive blank lines, and missing spaces around assignment operator (`total=len(...)`). | Wrapped statements within 79 characters, fixed operator whitespace, and normalized blank lines. |
