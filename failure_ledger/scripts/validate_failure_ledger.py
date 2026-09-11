"""Validate data and exact generated views; failure exits nonzero."""
import argparse
import sys
sys.dont_write_bytecode = True
from ledger import LANE, load, validate, views

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--initial', action='store_true', help='Require owner-authorized initial snapshot')
    args = parser.parse_args()
    try:
        records, observations = load()
        total = validate(records, observations, initial=args.initial)
        for name, content in views(records, observations).items():
            if (LANE / name).read_bytes() != content.encode('utf-8'):
                raise ValueError(f'{name}: stale or manually modified view; regenerate')
        print(f'PASS OFFICIAL_FAILURE_COUNT={total} TARGET=1000 REMAINING={max(0,1000-total)} PROGRESS={total/1000:.1%}')
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
