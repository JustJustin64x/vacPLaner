#!/usr/bin/env python3
"""Opt-in feasibility probe, NOT a production accommodation provider.

Only fixed public candidate pages and read-only guest quote forms. No guest
details, reservation submission, account, payment, arbitrary URL or model access.
Uses the existing DNS-pinned transport with an isolated, narrow probe policy.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bs4 import BeautifulSoup
from vacation_planner.core.planning.SearchContext import SearchContext
from vacation_planner.infrastructure.planning.ResearchHttp import ResearchHttp
from vacation_planner.infrastructure.planning.TripStore import TripStore, timestamp

PAGES = {
    'hotelpalatino.de': {'/', '/robots.txt'},
    'www.gastinlaa.at': {'/buchen/', '/robots.txt'},
    'booking.smoobu.com': {'/robots.txt'},
    'beds24.com': {'/robots.txt', '/booking2.php', '/api/ajax/getroomprice.php'},
}
BASE_KEYS = {'propid', 'ownerid', 'checkin', 'numnight', 'numadult',
             'numchild', 'lang', 'multiroom'}
FORM_KEYS = {'booking', 'width', 'page', 'limitstart', 'checkin_hide',
             'fdate_date', 'fdate_monthyear'}
ROOMS = ('15792', '15795', '15797', '474024')


def safe_url(url):
    if not isinstance(url, str) or len(url) > 2000 or any(ord(c) <= 32 or ord(c) >= 127 for c in url):
        raise ValueError('Invalid probe URL')
    p = urlsplit(url)
    if p.scheme != 'https' or p.username or p.password or p.port not in (None, 443) or p.fragment or '\\' in url:
        raise ValueError('Public HTTPS only')
    if p.path not in PAGES.get(p.hostname, set()):
        raise ValueError('Outside fixed probe pages')
    q = parse_qs(p.query, keep_blank_values=True, strict_parsing=True)
    if any(len(v) != 1 for v in q.values()):
        raise ValueError('Repeated parameters')
    if p.path == '/api/ajax/getroomprice.php':
        if set(q) != {'ro','ci','co','na','nc','of','nr','la','cu'}:
            raise ValueError('Only observed single-room price GET')
        if q['ro'] not in (['163892'], ['608775'], ['300523'], ['300521']):
            raise ValueError('Unknown observed room')
        if q['of'] != ['1'] or q['nc'] != ['0'] or q['la'] != ['de'] or q['cu'] != ['']:
            raise ValueError('Unexpected tariff parameters')
        if q['na'] not in (['1'], ['2']) or q['nr'] not in (['1'], ['3']):
            raise ValueError('Unbounded occupancy')
        if q['ci'] != ['2026-11-23'] or q['co'] != ['2026-11-25']:
            raise ValueError('Outside fixed comparison dates')
        return url
    if p.path != '/booking2.php':
        if q:
            raise ValueError('Unexpected page parameters')
        return url
    room_keys = {prefix + '-'+room for room in ROOMS for prefix in ('sr1', 'na1', 'nc1', 'br1')}
    if set(q) - BASE_KEYS - FORM_KEYS - room_keys:
        raise ValueError('Unknown quote parameter; guest/payment submission forbidden')
    if q.get('propid') not in (['6949'], ['70716'], ['134588']):
        raise ValueError('Unknown property')
    if 'ownerid' in q and q['ownerid'] != ['40690']:
        raise ValueError('Unknown owner')
    if 'booking' in q and not re.fullmatch(r'[a-zA-Z0-9]{16,64}', q['booking'][0]):
        raise ValueError('Invalid ephemeral quote session')
    if 'page' in q and q['page'] != ['dates']:
        raise ValueError('Only initial search form may be submitted')
    if any(k.startswith('br1-') for k in q) and q.get('propid') != ['6949']:
        raise ValueError('Only observed Palatino quote form supported')
    return url


def redact_url(url):
    p = urlsplit(url)
    q = parse_qs(p.query, keep_blank_values=True)
    q.pop('booking', None)
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode({k:v[0] for k,v in q.items()}), ''))


class ProbeHttp(ResearchHttp):
    validate_url = staticmethod(safe_url)

    def __init__(self, store):
        super().__init__(store)
        self.wire_records = []
        self.last_beds_request = 0.0

    def _wire(self, url, ip, context, maximum, request_headers=None):
        # Conservative five-second spacing also for the initial robots fetch.
        if urlsplit(url).hostname == 'beds24.com':
            context.wait(max(0, 5.1 - (time.monotonic() - self.last_beds_request)))
        started = time.monotonic()
        try:
            r = super()._wire(url, ip, context, maximum, request_headers)
            self.wire_records.append(dict(url=redact_url(url), retrieved_at=timestamp(),
                status=r['status'], content_type=r['headers'].get('content-type'),
                bytes=len(r['body']), sha256=hashlib.sha256(r['body']).hexdigest(),
                seconds=round(time.monotonic()-started, 3)))
            return r
        finally:
            if urlsplit(url).hostname == 'beds24.com':
                self.last_beds_request = time.monotonic()


def value(node):
    if node.name == 'select':
        option = node.select_one('option[selected]') or node.select_one('option')
        return option.get('value', option.get_text()) if option else ''
    return node.get('value', '')


def summarize(html):
    soup = BeautifulSoup(html, 'html.parser')
    controls = {n['name']:value(n) for n in soup.select('input[name],select[name]')
                if (n['name'] in BASE_KEYS | {'firstnight', 'lastnight', 'checkout', 'subtotalprice', 'subtotaltax'}
                or re.fullmatch(r'(sr1|na1|nc1)-\d+', n['name']))
                and (n.get('type') != 'checkbox' or n.has_attr('checked'))}
    prices = []
    for node in soup.select('[id^="at_roomofferpriceofferid"]')[:12]:
        cell = node.find_parent('td') or node.parent
        selector = cell.select_one('select[name^="sr1-"]')
        prices.append(dict(id=node.get('id'), text=node.get_text(' ', strip=True),
            displayed_adult_icons=len(cell.select('img.pricenumadultimg')),
            selectable_units=[o.get('value') for o in selector.select('option')] if selector else []))
    for n in soup.select('script,style,select,nav,header,footer'):
        n.decompose()
    text = soup.get_text(' ', strip=True)
    # Keep bounded original context only; no complete webpage archive in report.
    total = soup.select_one('.book_totalprice')
    excerpt = total.parent.get_text(' ', strip=True)[:200] if total else ''
    return dict(controls=controls, price_cells=prices, quote_excerpt=excerpt,
                total_is_group_price=False,
                warning='Search price cells alone do not prove the requested room allocation.'), soup


def quote_form(html):
    soup = BeautifulSoup(html, 'html.parser')
    form = next(f for f in soup.select('form') if f.select_one('[name="sr1-15792"]'))
    if form.get('method', 'get').lower() != 'get' or form.get('action'):
        raise ValueError('Observed read-only GET form changed')
    q = {}
    for node in form.select('input[name],select[name]'):
        if node.get('type') == 'submit' or (node.get('type') == 'checkbox' and not node.has_attr('checked')):
            continue
        q[node['name']] = value(node)
    q.update({'multiroom':'1', 'sr1-15792':'2', 'sr1-15797':'1',
              'na1-15792':'2', 'na1-15797':'1', 'br1-15792':'Buchen'})
    return 'https://beds24.com/booking2.php?' + urlencode(q)


def run(output, responsive_only=False, selected_case=None):
    report = dict(schema_version=1, purpose='Step 1 feasibility, not application integration',
                  started_at=timestamp(), limits=dict(http=32, seconds=300, bytes=2_000_000,
                  beds24_spacing_seconds=5.1), cases=[], wire=[])
    context = SearchContext(seconds=300, budget=32)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vac-lodging-probe-') as directory:
        http = ProbeHttp(TripStore(Path(directory)/'probe.sqlite3'))
        def save():
            report.update(wire=http.wire_records, http_calls=context.calls, finished_at=timestamp())
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        def fetch(name, url, request=None):
            case = dict(name=name, url=redact_url(url), request=request)
            report['cases'].append(case)
            started = time.monotonic()
            try:
                # This observed guest endpoint deliberately returns JSON as text/plain.
                types = ('text/plain', 'application/json') if urlsplit(url).path == '/api/ajax/getroomprice.php' else ('text/html',)
                r = http.fetch(url, context, types=types)
                html = r['body'].decode('utf-8')
                if urlsplit(url).path == '/api/ajax/getroomprice.php':
                    parsed = json.loads(html)
                    case.update(status='retrieved', retrieved_at=r['retrieved_at'], response=parsed)
                    return html
                data, soup = summarize(html)
                case.update(status='retrieved', retrieved_at=r['retrieved_at'], data=data)
                if urlsplit(url).hostname != 'beds24.com':
                    case['booking_links'] = list(dict.fromkeys(n.get('href') or n.get('src')
                        for n in soup.select('a[href],iframe[src]')
                        if 'beds24.com/' in (n.get('href') or n.get('src') or '')))[:6]
                return html
            except (OSError, ValueError, InterruptedError) as exc:
                case.update(status='blocked_or_failed', error=str(exc))
                return None
            finally:
                case['seconds'] = round(time.monotonic()-started, 3)
                save()
                print(name, case['status'], case['seconds'], flush=True)

        if responsive_only:
            for name, room, adults, units in [
                ('laa-regular-room-two-adults', '163892', 2, 1),
                ('laa-three-units-same-room-type', '163892', 2, 3),
                ('heidelberg-room-two-adults', '300523', 2, 1),
                ('heidelberg-double-two-adults', '300521', 2, 1),
            ]:
                if selected_case and name != selected_case:
                    continue
                q = dict(ro=room, ci='2026-11-23', co='2026-11-25', na=adults,
                         nc=0, of=1, nr=units, la='de', cu='')
                fetch(name, 'https://beds24.com/api/ajax/getroomprice.php?'+urlencode(q),
                      dict(adults_per_unit=adults, units=units, checkin=q['ci'], checkout=q['co']))
            save()
            return report
        fetch('palatino-official-identity', 'https://hotelpalatino.de/')
        fetch('laa-official-identity', 'https://www.gastinlaa.at/buchen/')
        # This intentionally exercises the existing conservative robots policy.
        fetch('smoobu-robots-diagnostic', 'https://booking.smoobu.com/robots.txt')
        for name, prop, checkin, nights, adults, rooms in [
            ('palatino-two-adults-one-room', '6949', '2026-11-23', 2, 2, 1),
            ('palatino-five-adults-three-rooms', '6949', '2026-11-23', 2, 5, 3),
            ('palatino-july-five-adults-three-rooms', '6949', '2027-07-05', 6, 5, 3),
            ('laa-two-adults-one-room', '70716', '2026-11-23', 2, 2, 1),
            ('laa-five-adults-three-rooms', '70716', '2026-11-23', 2, 5, 3),
            ('heidelberg-two-adults-one-room', '134588', '2026-11-23', 2, 2, 1),
        ]:
            if date.fromisoformat(checkin) <= date.today():
                report['cases'].append(dict(name=name, status='skipped_past_date'))
                continue
            request = dict(checkin=checkin, nights=nights, adults=adults, rooms=rooms,
                           allocation=[2,2,1] if rooms==3 else [2])
            q = dict(propid=prop, checkin=checkin, numnight=nights, numadult=adults,
                     numchild=0, lang='de', multiroom=int(rooms>1))
            html = fetch(name, 'https://beds24.com/booking2.php?'+urlencode(q), request)
            if html and prop=='6949' and rooms==3:
                try:
                    url = quote_form(html)
                except (ValueError, StopIteration) as exc:
                    report['cases'].append(dict(name=name+'-quote', status='form_changed', error=str(exc)))
                    save()
                else:
                    fetch(name+'-quote', url, request)
        save()
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Explicitly perform public requests')
    parser.add_argument('--responsive-only', action='store_true', help='Four bounded GETs observed in responsive guest page scripts')
    parser.add_argument('--case', choices=['laa-regular-room-two-adults', 'laa-three-units-same-room-type',
                        'heidelberg-room-two-adults', 'heidelberg-double-two-adults'])
    parser.add_argument('--output', type=Path, default=Path('tmp/accommodation-access-2026-11-09/probe.json'))
    args = parser.parse_args()
    if not args.live:
        parser.error('Network probe requires --live; no application integration is performed.')
    if args.case and not args.responsive_only:
        parser.error('--case requires --responsive-only')
    run(args.output, args.responsive_only, args.case)
