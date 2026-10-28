# STRATEGY

The migration is a replace-the-edge strategy, not a rewrite strategy.

Keep the proven domain contract and replace the weakest fast-parser implementation behind an adapter. Use AnyDoc where deterministic local parsing is stronger, Kelpie where visual inference is required, and Python only for coordination and auditable output.

Success means fewer fragile heuristics and fewer Kelpie calls without losing provenance, failure isolation, or the ability to roll back to the existing parser.
