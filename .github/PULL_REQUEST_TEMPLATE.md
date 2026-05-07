## Summary

What changed?

## Why

Why is this change needed?

## Verification

- [ ] `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\run_tests.ps1 -q`
- [ ] `npm run build` in `apps/dashboard-web`
- [ ] `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ops\tools\smoke_local.ps1` when API/dashboard behavior changes
- [ ] Other verification described below

Verification details:

## Operator Impact

What should an owner, operator, or deployer know about this change?

## Documentation

- [ ] README updated if needed
- [ ] Runbooks updated if needed
- [ ] Dashboard or owner-facing copy updated if needed
