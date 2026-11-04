
#!/usr/bin/env python3
"""Reconcile the latest attempt of each payment transaction."""
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def timestamp(value):
    """Normalize ISO 8601 timestamps so timezone offsets compare correctly."""
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def reconcile(path):
    latest = {}
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, UnicodeError):
                continue
            if not isinstance(event, dict) or not event.get('txn_id'):
                continue
            txn_id = event['txn_id']
            event_time = timestamp(event['ts'])
            if txn_id not in latest or event_time > latest[txn_id][0]:
                latest[txn_id] = (event_time, event)

    successes = [event for _, event in latest.values() if event['status'] == 'success']
    total = sum(
        (Decimal(str(event['amount']).replace(',', '')) for event in successes),
        Decimal('0')
    )
    return len(successes), total


def main():
    count, total = reconcile(ROOT / 'payments.jsonl')
    expected = int((ROOT / 'expected.txt').read_text(encoding='utf-8').strip())
    if count != expected:
        print(f'Check failed: counted {count} successful payments, expected {expected}.')
        print("Something in the data isn't being handled the way the README describes.")
    else:
        print(f'Check passed: {count} successful payments.')
        print(f'Your code: KOYA-{round(total)}')


if __name__ == '__main__':
    main()
