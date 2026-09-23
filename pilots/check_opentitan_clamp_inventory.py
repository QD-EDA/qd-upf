#!/usr/bin/env python3
"""Replay the pinned collateral inventory; never evaluate Tcl or certify UPF."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qd_upf import lex, split_list, check


def main():
    if len(sys.argv) != 2:
        print('usage: check_opentitan_clamp_inventory.py OPENTITAN_ROOT', file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    inventory = json.loads(Path(__file__).with_name('opentitan-clamp-inventory.json').read_text())
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True)
        if revision != inventory['revision'] or dirty:
            raise ValueError('expected clean pinned OpenTitan checkout')
        source = (root / inventory['source']).read_bytes()
        if hashlib.sha256(source).hexdigest() != inventory['source_sha256']:
            raise ValueError('collateral content differs from recorded source hash')
        commands = lex(source.decode('utf-8'))
        if (len(commands) != 1 or len(commands[0]) != 3 or
                [word for word, _ in commands[0][:2]] != ['set', 'UPF_ISO_LC_OFF_PORTS_CLAMP1']):
            raise ValueError('unexpected collateral structure')
        ports = split_list(commands[0][2][0])
        if [{'port': port, 'clamp': '1'} for port in ports] != inventory['requirements']:
            raise ValueError('recorded requirements differ from collateral')
        report = check(source.decode('utf-8'), inventory['source'], [], 'no-topology.json')
        if (report['result'] != 'error' or len(report['diagnostics']) != 1 or
                report['diagnostics'][0]['code'] != 'UNSUPPORTED'):
            raise ValueError('upstream Tcl must not be mistaken for supported UPF intent')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'inventory replay: {error}', file=sys.stderr)
        return 2
    print(json.dumps(inventory, indent=2, sort_keys=True))
    return 3  # Inventory reproduced, power-intent qualification still UNKNOWN.


if __name__ == '__main__':
    raise SystemExit(main())
