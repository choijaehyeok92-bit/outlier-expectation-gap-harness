# Recorded US quote fixtures

Shaped like the published responses of Polygon.io (`grouped_daily`,
`ticker_range`) and EODHD (`eod-bulk-last-day`). **The numbers are
invented.** This environment has never reached either venue, so no real
quote could be recorded; what these files pin down is the parsing — field
names, the epoch-to-session-date conversion, the `.US` suffix, and an
empty response meaning "no trading session", not "no data".

To refresh from a live vendor once a key and egress exist, wrap the real
transport in `data_adapters.testing.RecordingTransport` pointed at this
directory. Key parameters are stripped from fixture filenames, so a
recording cannot carry a credential into the repository.
