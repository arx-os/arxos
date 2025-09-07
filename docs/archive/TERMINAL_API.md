# Terminal API Quick Reference

Common commands relevant to onboarding and RF operations.

## Invites
```
invite generate <viewer|tech|admin> <hours>
invite accept <13B-hex>
```

## Mobile Offline Binder (loopback demo)
```
mobile init
mobile send <13B-hex> [13B-hex...]
mobile recv
```

## Latency Estimator
```
latency <objects> [hops=1] [profile=range|speed]
```

## Document Links
- Onboarding workflow: `docs/ONBOARDING_WORKFLOW.md`
- Day-of-scan checklist: `docs/DAY_OF_SCAN_CHECKLIST.md`
- Latency estimates: `docs/LATENCY_ESTIMATES.md`
- Feature flags: `docs/FEATURE_FLAGS.md`
