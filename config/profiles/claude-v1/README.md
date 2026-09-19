# Historical v2 calibration profile

These JSON files and `../_original/` are archived policy references, not v3 runtime configuration.
Use their original Git commit in a separate checkout for exact historical replay. `apply.sh`
and `revert.sh` now refuse to overwrite the v3 configuration, because doing so would restore
retired archetypes and silently change investment policy. New work uses `config/*.json`.
