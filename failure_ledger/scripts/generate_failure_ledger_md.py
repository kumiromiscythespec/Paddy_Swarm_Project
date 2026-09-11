"""Generate only two review views after validating data."""
import sys
sys.dont_write_bytecode = True
from ledger import LANE, load, validate, views

def main():
    try:
        records, observations = load()
        validate(records, observations)
        for name, content in views(records, observations).items():
            (LANE / name).write_bytes(content.encode('utf-8'))
        print('PASS generated FAILURE_LEDGER.md and KNOWN_UNMAPPED_FAILURES.md')
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
