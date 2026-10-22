# qd-upf

Conservative static checker for a subset of UPF power intent (not a power-aware simulator, not signoff).

```sh
./qd-upf check examples/valid.upf --topology examples/crossings.json
python3 -m unittest -v
```

Full usage, limits and scope: [docs/usage.md](docs/usage.md). Spec: [SPEC.md](SPEC.md).

Status: active prototype (Sep 2026).
