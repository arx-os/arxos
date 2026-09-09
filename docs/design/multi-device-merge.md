# Multi-device merge invariants

## Three-way object set merge

Concurrent tips are merged relative to their nearest common ancestor on the
`previous_root ∪ merge_parents` DAG (not naive set union).

```
result = (base ∪ adds_a ∪ adds_b) − removes_a − removes_b
```

### Consequences

| Concurrent actions | Result |
|--------------------|--------|
| A removes entity E; B keeps E | E **removed** |
| A and B both add distinct objects | **Union** of adds |
| A updates entity E (v1→v2); B removes v1 | **v2 kept** (add of v2 is independent of remove of v1) |
| A removes controller; B authors with old set | After merge to A's building, B **cannot** author |
| Fast-forward (A ancestor of B) | Result = B's active set |

## Post-set collapse

1. Entity collapse (one version per `EntityId`)
2. Building collapse (one Building object per `building_id`)
3. Annotation proximity dedupe

## Operator rule

Always pull the other tip's objects into the local store before `merge apply`.
Metadata-first pulls omit blobs and **must not** set head (`--no-set-head`).
`merge apply` of a parent whose authors are not local controllers is rejected
(Authorization); untrusted objects cannot enter official history.
