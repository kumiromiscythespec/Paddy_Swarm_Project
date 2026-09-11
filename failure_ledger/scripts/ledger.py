"""Standard-library validation and deterministic views; no Git operations."""
import datetime
import json
from pathlib import Path
import re

LANE = Path(__file__).resolve().parents[1]
INITIAL_IDS = {f'F-{i:04d}' for i in range(1, 51)}
FIELDS = set('failure_id official_count_member date date_status component version specimen test expected_result actual_result classification failure_mode count_status root_cause root_cause_status evidence duplicate_of legacy_record detail_status notes qualification'.split())
CHECKS = 'physical_specimen_exists physical_activity_performed expected_result_defined expectation_not_met uniqueness_checked independent_failure_unit evidence_exists'.split()
CLASSES = {'PHYSICAL_FAIL', 'DUPLICATE', 'CAD_FAIL', 'PREFLIGHT_FAIL', 'REJECTED_BEFORE_BUILD', 'SUPERSEDED_UNVALIDATED', 'TEST_NOT_PERFORMED'}
STATUSES = {'COUNTED', 'NOT_COUNTED', 'HOLD', 'ID_MAPPING_PENDING'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def counted(r):
    return r['classification'] == 'PHYSICAL_FAIL' and r['count_status'] == 'COUNTED'

def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result

def load():
    records = []
    for n, line in enumerate((LANE / 'FAILURE_LEDGER.jsonl').read_text(encoding='utf-8').splitlines(), 1):
        require(bool(line.strip()), f'Blank JSONL line {n}')
        records.append(json.loads(line, object_pairs_hook=unique_keys))
    observations = json.loads((LANE / 'KNOWN_UNMAPPED_FAILURES.json').read_text(encoding='utf-8'), object_pairs_hook=unique_keys)
    return records, observations

def validate(records, observations, initial=False):
    ids = set()
    for r in records:
        require(isinstance(r, dict) and FIELDS <= r.keys(), 'Missing required fields')
        fid = r['failure_id']
        require(isinstance(fid, str) and re.fullmatch(r'F-[0-9]{4,}', fid) is not None and int(fid[2:]) > 0 and fid == f'F-{int(fid[2:]):04d}', f'Invalid ID: {fid}')
        require(fid not in ids, f'Duplicate ID: {fid}')
        ids.add(fid)
        require(r['classification'] in CLASSES and r['count_status'] in STATUSES, f'{fid}: invalid enum')
        require(type(r['legacy_record']) is bool, f'{fid}: legacy_record must be boolean')
        require(type(r['official_count_member']) is bool and r['official_count_member'] == counted(r), f'{fid}: official_count_member disagrees with derived predicate')
        require(r['count_status'] != 'COUNTED' or r['classification'] == 'PHYSICAL_FAIL', f'{fid}: COUNTED requires PHYSICAL_FAIL')
        require(r['date_status'] in {'UNKNOWN', 'CONFIRMED'}, f'{fid}: invalid date_status')
        if r['date'] is None:
            require(r['date_status'] == 'UNKNOWN', f'{fid}: missing confirmed date')
        else:
            require(isinstance(r['date'], str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', r['date']) is not None, f'{fid}: date must be YYYY-MM-DD')
            datetime.date.fromisoformat(r['date'])
            require(r['date_status'] == 'CONFIRMED', f'{fid}: date not confirmed')
        for field in 'component version specimen test expected_result actual_result failure_mode root_cause notes'.split():
            require(r[field] is None or isinstance(r[field], str), f'{fid}: invalid {field}')
        require(r['detail_status'] in {'LEGACY_DETAIL_NOT_RECONSTRUCTED', 'RECONSTRUCTION_PENDING', 'PARTIAL', 'DOCUMENTED'}, f'{fid}: invalid detail_status')
        require(r['root_cause_status'] in {'NOT_ESTABLISHED', 'OWNER_REPORTED', 'EVIDENCE_SUPPORTED'}, f'{fid}: invalid root cause status')
        require(r['root_cause_status'] != 'NOT_ESTABLISHED' or r['root_cause'] is None, f'{fid}: unestablished root cause must be null')
        require(isinstance(r['evidence'], list), f'{fid}: evidence must be list')
        for e in r['evidence']:
            require(isinstance(e, dict) and {'type', 'reference', 'scope'} <= e.keys(), f'{fid}: invalid evidence')
            require(e['type'] in {'repository_path', 'test_report', 'cad_path', 'photo', 'video', 'youtube_url', 'git_commit', 'note_url', 'external_url', 'owner_statement'}, f'{fid}: evidence type')
            require(all(isinstance(e[k], str) and e[k].strip() for k in ('reference', 'scope')), f'{fid}: empty evidence')
            if e['type'] == 'git_commit':
                require(re.fullmatch(r'[0-9a-fA-F]{40}', e['reference']) is not None, f'{fid}: invalid commit SHA')
            if e['type'] in {'youtube_url', 'note_url', 'external_url'}:
                require(re.match(r'https?://[^/\s]+', e['reference']) is not None, f'{fid}: invalid URL')
            if e['type'] in {'repository_path', 'cad_path', 'owner_statement'}:
                target = (LANE.parent / e['reference']).resolve()
                require(target.is_relative_to(LANE.parent) and target.is_file(), f'{fid}: missing repository evidence')
        q = r['qualification']
        require(isinstance(q, dict) and set(q) == set(CHECKS) and all(type(v) is bool or v is None for v in q.values()), f'{fid}: invalid qualification')
        if counted(r) and fid not in INITIAL_IDS:
            require(not r['legacy_record'] and all(v is True for v in q.values()), f'{fid}: unconfirmed new COUNTED failure')
            require(r['detail_status'] == 'DOCUMENTED' and bool(r['evidence']), f'{fid}: new failure needs documented evidence')
            require(all(r[k] and r[k] not in {'UNKNOWN', 'RECONSTRUCTION_PENDING', 'NOT_ESTABLISHED'} for k in ('component', 'specimen', 'test', 'expected_result', 'actual_result')), f'{fid}: new failure lacks physical details')
        require(not r['legacy_record'] or fid in INITIAL_IDS, f'{fid}: legacy exemption limited to initial IDs')
        require(r['duplicate_of'] is None or isinstance(r['duplicate_of'], str), f'{fid}: duplicate target type')
        require(r['duplicate_of'] != fid, f'{fid}: self duplicate')
        require(r['duplicate_of'] is None or not counted(r), f'{fid}: duplicate cannot count')
        require(r['classification'] != 'DUPLICATE' or r['duplicate_of'] is not None, f'{fid}: duplicate target required')
    by_id = {r['failure_id']: r for r in records}
    for r in records:
        require(r['duplicate_of'] is None or r['duplicate_of'] in ids, f"{r['failure_id']}: missing duplicate target")
    for r in records:
        seen = set()
        current = r
        while current['duplicate_of'] is not None:
            require(current['failure_id'] not in seen, 'Duplicate cycle')
            seen.add(current['failure_id'])
            current = by_id[current['duplicate_of']]
    observation_ids = set()
    for o in observations:
        require(set(o) == {'observation_id', 'component', 'classification', 'count_status', 'maximum_candidates', 'notes', 'source_paths'}, 'Invalid observation fields')
        require(isinstance(o['observation_id'], str) and re.fullmatch(r'OBS-[0-9]{3}', o['observation_id']) is not None and o['observation_id'] not in observation_ids, 'Invalid observation ID')
        observation_ids.add(o['observation_id'])
        require(o['count_status'] in STATUSES - {'COUNTED'}, 'Observations cannot count')
        require(o['classification'] in CLASSES | {'PHYSICAL_FAILURE_CONFIRMED_OR_REPORTED'}, 'Invalid observation class')
        require(o['maximum_candidates'] is None or (type(o['maximum_candidates']) is int and o['maximum_candidates'] > 0), 'Invalid candidate bound')
        require(isinstance(o['source_paths'], list), 'Invalid source paths')
        for p in o['source_paths']:
            target = (LANE.parent / p).resolve()
            require(target.is_relative_to(LANE.parent) and target.is_file(), f'Missing source: {p}')
    total = sum(counted(r) for r in records)
    if initial:
        require(ids == INITIAL_IDS and total == 50, 'Initial snapshot requires exactly F-0001..F-0050, all counted')
        for r in records:
            number = int(r['failure_id'][2:])
            expected = 'LEGACY_DETAIL_NOT_RECONSTRUCTED' if number <= 46 else 'PARTIAL' if number == 47 else 'RECONSTRUCTION_PENDING'
            require(r['detail_status'] == expected and r['legacy_record'], 'Initial detail status mismatch')
        require(len(observations) == 7 and sum(o['count_status'] == 'HOLD' for o in observations) == 1 and sum(o['count_status'] == 'ID_MAPPING_PENDING' for o in observations) == 3, 'Initial observation mismatch')
    return total

def cell(value):
    return str(value if value is not None else 'UNKNOWN').replace('&', '&amp;').replace('<', '&lt;').replace('|', '&#124;').replace('\n', '<br>')

def render(records, observations):
    total = sum(counted(r) for r in records)
    lines = ['# Paddy Swarm FAILURE COUNT', '', '<!-- GENERATED: do not edit; source FAILURE_LEDGER.jsonl -->', '', f'{total} / 1000', '', f'Remaining: {max(0, 1000-total)}', '', f'Progress: {total / 1000:.1%}', '', 'COUNT is derived only from PHYSICAL_FAIL + COUNTED records.', 'Observation groups never contribute to COUNT; their overlap is unresolved.', '', '## COUNTED physical FAIL', '', '| ID | Component | Actual result | Failure mode | Detail status |', '|---|---|---|---|---|']
    for r in sorted(records, key=lambda x: int(x['failure_id'][2:])):
        if counted(r):
            lines.append('| ' + ' | '.join(cell(r[k]) for k in ('failure_id', 'component', 'actual_result', 'failure_mode', 'detail_status')) + ' |')
    for status in ('HOLD', 'ID_MAPPING_PENDING'):
        rr = [r for r in records if r['count_status'] == status]
        oo = [o for o in observations if o['count_status'] == status]
        lines += ['', f'## {status}', '', f'Ledger records: {len(rr)}; observation groups: {len(oo)}.', '']
        lines += [f"- {r['failure_id']}: {cell(r['component'])}" for r in rr]
        lines += [f"- {o['observation_id']}: {cell(o['component'])}; maximum candidates: {cell(o['maximum_candidates'])}. {cell(o['notes'])}" for o in oo]
    pending = [r for r in records if r['detail_status'] == 'RECONSTRUCTION_PENDING']
    legacy = [r for r in records if r['detail_status'] == 'LEGACY_DETAIL_NOT_RECONSTRUCTED']
    lines += ['', '## RECONSTRUCTION_PENDING', '', f'Exact status: {len(pending)} records (' + ', '.join(r['failure_id'] for r in pending) + ').', f'LEGACY_DETAIL_NOT_RECONSTRUCTED: {len(legacy)} additional records.', 'These are subsets of COUNTED records, not extra failures.', '', '## NON_COUNTED engineering rejection', '']
    lines += [f"- {o['observation_id']}: {cell(o['component'])} / {o['classification']} / {o['count_status']}" for o in observations if o['count_status'] == 'NOT_COUNTED']
    lines += [f"- {r['failure_id']}: {cell(r['component'])} / {r['classification']} / {r['count_status']}" for r in records if r['count_status'] == 'NOT_COUNTED']
    lines += ['', 'TEST_NOT_PERFORMED, CAD_FAIL, PREFLIGHT_FAIL, REJECTED_BEFORE_BUILD,', 'SUPERSEDED_UNVALIDATED and DUPLICATE contribute zero.', '', 'Source details: [JSONL](FAILURE_LEDGER.jsonl), [unmapped observations](KNOWN_UNMAPPED_FAILURES.md).', '']
    return '\n'.join(lines)

def render_observations(observations):
    lines = ['# Known unmapped failures and exclusions', '', '<!-- GENERATED from KNOWN_UNMAPPED_FAILURES.json; do not edit -->', '', 'OBS IDs identify intake groups, not formal FAILURE_IDs or official count members.', 'Maximum candidates are upper bounds, not established unique failure counts.', 'Candidate B may overlap the lower-cradle group and the existing 50 records.', 'No physical test date is inferred from a repository/commit date.', '']
    for o in observations:
        lines += [f"## {o['observation_id']} — {o['component']}", '', f"Classification: {o['classification']}", f"COUNT_STATUS={o['count_status']}", f"Maximum candidates: {cell(o['maximum_candidates'])}", '', o['notes'], '', 'Sources: [owner intake](INITIAL_OWNER_STATEMENT.md).', '']
        lines += [f'- [{p}](../{p})' for p in o['source_paths']]
        lines.append('')
    return '\n'.join(lines)

def views(records, observations):
    return {'FAILURE_LEDGER.md': render(records, observations), 'KNOWN_UNMAPPED_FAILURES.md': render_observations(observations)}
