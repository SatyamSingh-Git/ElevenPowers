# stockroom

Track items, locations and stock movements in a single JSON file.

    stockroom add-location A1 --kind shelf
    stockroom add-item BOLT-M6 "M6 bolt" --reorder 20 --cost 0.12
    stockroom receive BOLT-M6 100 A1
    stockroom low

See `docs/reference.md` for options, the data file and error messages.
