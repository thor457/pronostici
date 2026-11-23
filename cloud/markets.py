"""Addestramento su tutti i mercati dei bookmaker con le statistiche ufficiali partita per partita
(football-data.co.uk: gol, primo tempo, tiri, tiri in porta, falli, corner, gialli, rossi, arbitro, quote 1X2 / O-U 2,5 / handicap
asiatico di apertura e chiusura) per le stagioni 2025-26 e 2026-27 di 22 campionati.

Per ogni partita, in ordine di data, il pronostico si fa con i SOLI dati delle gare precedenti (medie fatte/subite di squadra,
in casa e fuori, arbitro per i cartellini, restringimento verso la media del campionato), poi si confronta con il risultato.
Scrive state/markets.json: medie di squadra e arbitri aggiornate (per i pronostici dell'app) e i risultati per mercato.
Uso: python3 cloud/markets.py [cartella_csv_gia_scaricati]
"""
import csv, io, json, math, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEAGUES = {'I1': 'Serie A', 'I2': 'Serie B', 'E0': 'Premier League', 'E1': 'Championship', 'E2': 'League One', 'E3': 'League Two',
           'EC': 'National League', 'SP1': 'LaLiga', 'SP2': 'LaLiga 2', 'D1': 'Bundesliga', 'D2': '2. Bundesliga', 'F1': 'Ligue 1',
           'F2': 'Ligue 2', 'N1': 'Eredivisie', 'B1': 'Pro League', 'P1': 'Primeira Liga', 'T1': 'Süper Lig', 'G1': 'Super League Grecia',
           'SC0': 'Premiership', 'SC1': 'Championship SCO', 'SC2': 'League One SCO', 'SC3': 'League Two SCO'}
SEASONS = ['2526', '2627']
# statistica -> (colonna casa, colonna ospite)
STATS = {'g': ('FTHG', 'FTAG'), 'g1': ('HTHG', 'HTAG'), 's': ('HS', 'AS'), 'st': ('HST', 'AST'), 'f': ('HF', 'AF'),
         'c': ('HC', 'AC'), 'y': ('HY', 'AY'), 'r': ('HR', 'AR')}
NAMES = {'g': 'Gol', 'g1': 'Gol 1° tempo', 's': 'Tiri', 'st': 'Tiri in porta', 'f': 'Falli', 'c': 'Corner', 'y': 'Gialli', 'r': 'Rossi'}
K = 6.0  # partite "virtuali" di restringimento verso la media del campionato


def fetch(lg, ss, cache):
    p = os.path.join(cache, lg + '_' + ss + '.csv') if cache else None
    if p and os.path.exists(p) and os.path.getsize(p) > 200:
        return open(p, encoding='utf-8-sig', errors='replace').read()
    url = 'https://www.football-data.co.uk/mmz4281/%s/%s.csv' % (ss, lg)
    for _ in range(3):
        r = subprocess.run(['curl', '-sL', '-m', '40', url], capture_output=True)
        if r.returncode == 0 and len(r.stdout) > 200:
            return r.stdout.decode('utf-8-sig', errors='replace')
        time.sleep(2)
    return ''


def num(x):
    try:
        return float(x)
    except Exception:
        return None


def ddate(d):
    p = d.split('/')
    if len(p) != 3: return ''
    y = p[2] if len(p[2]) == 4 else '20' + p[2]
    return y + '-' + p[1] + '-' + p[0]


def nb_over(m, r, line):
    """P(X > line) con X binomiale negativa (media m, dispersione r); r grande = Poisson"""
    m = max(m, 1e-6)
    if r > 500:
        c = math.exp(-m); s = c
        for k in range(1, int(line) + 1):
            c *= m / k; s += c
        return 1 - s
    p = r / (r + m); c = p ** r; s = c
    for k in range(1, int(line) + 1):
        c = c * (k - 1 + r) / k * (1 - p); s += c
    return max(0.0, min(1.0, 1 - s))


def pois(m, k):
    return math.exp(-m) * m ** k / math.factorial(k)


class Team:
    def __init__(self):
        self.h = {}; self.a = {}  # stat -> [n, fatti, subiti] in casa / fuori

    def add(self, side, st, f, s):
        d = self.h if side == 'h' else self.a
        x = d.setdefault(st, [0, 0.0, 0.0]); x[0] += 1; x[1] += f; x[2] += s

    def rate(self, side, st, Lf, Ls, prior=None):
        """media fatti/subiti in casa (side h) o fuori (a), metà peso dall'altro campo, restringimento K"""
        o = self.h if side == 'h' else self.a; t = self.a if side == 'h' else self.h
        a = o.get(st, [0, 0, 0]); b = t.get(st, [0, 0, 0])
        n = a[0] + 0.5 * b[0]
        if n <= 0 and not prior: return Lf, Ls, 0
        # l'altro campo corretto per il vantaggio casa medio
        fo = a[1] + 0.5 * b[1] * (Lf / max(1e-6, Ls)) if b[0] else a[1]
        so = a[2] + 0.5 * b[2] * (Ls / max(1e-6, Lf)) if b[0] else a[2]
        pf, ps, pn = (prior if prior else (Lf, Ls, 0))
        kk = K + pn
        f = (fo + K * Lf + pn * pf) / (n + kk); s = (so + K * Ls + pn * ps) / (n + kk)
        return f, s, n


class Cal:
    """taratura imparata in corsa: per ogni mercato 10 fasce di probabilità -> frequenza vera (con restringimento)"""
    def __init__(self):
        self.t = {}

    def p(self, key, q):
        b = self.t.get(key)
        if not b: return q
        i = min(9, int(q * 10)); n, h = b[i]
        return (h + 12 * q) / (n + 12) if n else q

    def upd(self, key, q, o):
        b = self.t.setdefault(key, [[0, 0] for _ in range(10)]); i = min(9, int(q * 10)); b[i][0] += 1; b[i][1] += int(o)


class Eval:
    def __init__(self):
        self.m = {}

    def add(self, key, fam, label, lg, p, hit, pm=None):
        """p = probabilità del lato scelto (>= 0,5); pm = stessa probabilità secondo il mercato, se c'è"""
        for k in (key, key + '@' + lg):
            x = self.m.setdefault(k, {'fam': fam, 'label': label, 'n': 0, 'hit': 0, 'sp': 0.0, 'br': 0.0, 'sol_n': 0, 'sol_hit': 0,
                                      'bins': [[0, 0, 0.0] for _ in range(5)], 'mk_n': 0, 'mk_br': 0.0, 'mo_br': 0.0})
            x['n'] += 1; x['hit'] += hit; x['sp'] += p; x['br'] += (p - hit) ** 2
            if p >= 0.7: x['sol_n'] += 1; x['sol_hit'] += hit
            b = min(4, int((p - 0.5) / 0.1)); x['bins'][b][0] += 1; x['bins'][b][1] += hit; x['bins'][b][2] += p
            if pm is not None:
                x['mk_n'] += 1; x['mk_br'] += (pm - hit) ** 2; x['mo_br'] += (p - hit) ** 2


def implied(o):
    v = [num(x) for x in o]
    if any(x is None or x <= 1 for x in v): return None
    s = sum(1 / x for x in v); return [1 / x / s for x in v]


def run(cache=None):
    rows = []; lgavg = {}
    for ss in SEASONS:
        for lg in LEAGUES:
            txt = fetch(lg, ss, cache)
            if not txt: print('  manca', lg, ss); continue
            for r in csv.DictReader(io.StringIO(txt)):
                if not r.get('HomeTeam') or num(r.get('FTHG')) is None: continue
                r['_lg'] = lg; r['_ss'] = ss; r['_d'] = ddate(r.get('Date', '')) + ' ' + (r.get('Time') or '')
                rows.append(r)
    rows.sort(key=lambda r: r['_d'])
    print('partite:', len(rows))
    teams = {}; refs = {}; L = {}; prev = {}  # L[(lg,ss)][st] = [n, somma casa, somma ospite, somma quadrati totale]
    E = Eval(); disp = {}; CA = Cal(); pend = []
    # dispersione per statistica (varianza totale / media) stimata sulla stagione 2025-26 completa
    for st, (hc, ac) in STATS.items():
        v = [num(r.get(hc)) + num(r.get(ac)) for r in rows if r['_ss'] == '2526' and num(r.get(hc)) is not None and num(r.get(ac)) is not None]
        if len(v) > 50:
            m = sum(v) / len(v); var = sum((x - m) ** 2 for x in v) / len(v)
            disp[st] = m * m / (var - m) if var > m * 1.02 else 1e9
    print('dispersione:', {k: round(v, 1) for k, v in disp.items()})
    LINES = {'c': [7.5, 8.5, 9.5, 10.5, 11.5], 'y': [2.5, 3.5, 4.5, 5.5], 'st': [6.5, 7.5, 8.5, 9.5], 's': [20.5, 22.5, 24.5, 26.5],
             'f': [20.5, 22.5, 24.5, 26.5], 'g': [0.5, 1.5, 2.5, 3.5, 4.5], 'g1': [0.5, 1.5, 2.5]}
    TLINES = {'c': [2.5, 3.5, 4.5, 5.5, 6.5], 'y': [0.5, 1.5, 2.5], 'st': [2.5, 3.5, 4.5, 5.5], 's': [9.5, 11.5, 13.5], 'f': [9.5, 11.5, 13.5], 'g': [0.5, 1.5, 2.5]}
    for r in rows:
        lg, ss = r['_lg'], r['_ss']; key = (lg, ss); LL = L.setdefault(key, {})
        ht, at = r['HomeTeam'].strip(), r['AwayTeam'].strip()
        T = teams.setdefault((lg, ss, ht), Team()); U = teams.setdefault((lg, ss, at), Team())
        lab = LEAGUES[lg]
        ok_pred = True
        for t, tt in ((ht, T), (at, U)):
            n = sum(x[0] for x in [tt.h.get('g', [0]), tt.a.get('g', [0])])
            if n < 3: ok_pred = False
        lgn = LL.get('g', [0])[0]
        if lgn < 20: ok_pred = False
        val = {st: (num(r.get(hc)), num(r.get(ac))) for st, (hc, ac) in STATS.items()}
        if ok_pred:
            exp = {}
            for st in STATS:
                if st not in LL or val[st][0] is None: continue
                n0, sh, sa, _ = LL[st]; Lh, La = sh / n0, sa / n0
                pr_h = prev.get((lg, ht, st, 'h')); pr_a = prev.get((lg, at, st, 'a'))
                hf, hs, _ = T.rate('h', st, Lh, La, pr_h); af, as_, _ = U.rate('a', st, La, Lh, pr_a)
                eh = Lh * (hf / max(1e-6, Lh)) * (as_ / max(1e-6, Lh)); ea = La * (af / max(1e-6, La)) * (hs / max(1e-6, La))
                if st == 'y':
                    ref = (r.get('Referee') or '').strip(); rf = refs.get(ref)
                    if rf and rf[0] >= 3:
                        w = rf[0] / (rf[0] + 8.0); fac = (1 - w) + w * (rf[1] / rf[0]) / max(1e-6, (Lh + La))
                        eh *= fac; ea *= fac
                exp[st] = (eh, ea)
            for st, (eh, ea) in exp.items():
                tv = val[st][0] + val[st][1]; rr = disp.get(st, 1e9)
                for ln in LINES.get(st, []):
                    kb = '%s_T%s' % (st.upper(), ln); q = nb_over(eh + ea, rr, ln); po = CA.p(kb, q); o = tv > ln; pend.append((kb, q, o))
                    side = 'Over' if po >= 0.5 else 'Under'; p = po if po >= 0.5 else 1 - po; hit = int(o if po >= 0.5 else not o)
                    pm = None
                    if st == 'g' and ln == 2.5:
                        im = implied([r.get('Avg>2.5') or r.get('B365>2.5'), r.get('Avg<2.5') or r.get('B365<2.5')])
                        if im: pm = im[0] if po >= 0.5 else im[1]
                    E.add('%s_T%s_%s' % (st.upper(), ln, side[0]), NAMES[st], '%s totali %s %s' % (NAMES[st], side, str(ln).replace('.', ',')), lab, p, hit, pm)
                rr2 = rr * 0.5 if rr < 1e8 else rr
                for who, e1, v1, nm in (('H', eh, val[st][0], 'casa'), ('A', ea, val[st][1], 'ospite')):
                    for ln in TLINES.get(st, []):
                        kb = '%s_%s%s' % (st.upper(), who, ln); q = nb_over(e1, rr2, ln); po = CA.p(kb, q); o = v1 > ln; pend.append((kb, q, o))
                        side = 'Over' if po >= 0.5 else 'Under'; p = po if po >= 0.5 else 1 - po; hit = int(o if po >= 0.5 else not o)
                        E.add('%s_%s%s_%s' % (st.upper(), who, ln, side[0]), NAMES[st], '%s squadra di %s %s %s' % (NAMES[st], nm, side, str(ln).replace('.', ',')), lab, p, hit)
                # chi ne fa di più (1X2 della statistica), solo per corner, gialli, tiri in porta, tiri, falli
                if st in ('c', 'y', 'st', 's', 'f'):
                    if rr < 1e8:
                        # approssimazione: differenza di due binomiali negative ~ normale
                        sd = math.sqrt(eh + eh * eh / (rr / 2) + ea + ea * ea / (rr / 2))
                    else:
                        sd = math.sqrt(eh + ea)
                    z1 = (eh - ea - 0.5) / sd; z2 = (eh - ea + 0.5) / sd
                    ph = 0.5 * (1 + math.erf(z1 / math.sqrt(2))); pa = 1 - 0.5 * (1 + math.erf(z2 / math.sqrt(2))); pd = 1 - ph - pa
                    res = 'H' if val[st][0] > val[st][1] else ('A' if val[st][0] < val[st][1] else 'D')
                    best = max((ph, 'H'), (pa, 'A'), (pd, 'D'))
                    E.add('%s_1X2' % st.upper(), NAMES[st], '%s: chi ne fa di più (1X2)' % NAMES[st], lab, best[0], int(best[1] == res))
                    dc = max((ph + pd, 'HD'), (pa + pd, 'AD'))
                    E.add('%s_DC' % st.upper(), NAMES[st], '%s: doppia chance' % NAMES[st], lab, dc[0], int(res in dc[1]))
            # gol: 1X2, Goal/No Goal, esatto, handicap asiatico, contro il mercato
            if 'g' in exp:
                eh, ea = exp['g']; M = [[pois(eh, i) * pois(ea, j) for j in range(9)] for i in range(9)]
                ph = sum(M[i][j] for i in range(9) for j in range(9) if i > j); pa = sum(M[i][j] for i in range(9) for j in range(9) if i < j); pd = 1 - ph - pa
                hg, ag = int(val['g'][0]), int(val['g'][1]); res = 'H' if hg > ag else ('A' if hg < ag else 'D')
                im = implied([r.get('AvgH') or r.get('B365H'), r.get('AvgD') or r.get('B365D'), r.get('AvgA') or r.get('B365A')])
                # modello misto: dati + mercato (quote medie di chiusura se presenti)
                imc = implied([r.get('AvgCH') or r.get('B365CH'), r.get('AvgCD') or r.get('B365CD'), r.get('AvgCA') or r.get('B365CA')]) or im
                best = max((ph, 'H'), (pa, 'A'), (pd, 'D'))
                E.add('ESITO_1X2', 'Esito', 'Esito 1X2 (solo dati)', lab, best[0], int(best[1] == res), (im[['H', 'D', 'A'].index(best[1])] if im else None))
                if im:
                    mx = [0.5 * a + 0.5 * b for a, b in zip([ph, pd, pa], im)]; bi = max(range(3), key=lambda i: mx[i])
                    E.add('ESITO_MIX', 'Esito', 'Esito 1X2 (dati + mercato)', lab, mx[bi], int('HDA'[bi] == res))
                    bi = max(range(3), key=lambda i: im[i])
                    E.add('ESITO_MKT', 'Esito', 'Esito 1X2 (solo quote di apertura)', lab, im[bi], int('HDA'[bi] == res))
                dc = max((ph + pd, 'HD', '1X'), (pa + pd, 'AD', 'X2'), (ph + pa, 'HA', '12'))
                E.add('DOPPIA', 'Esito', 'Doppia chance', lab, dc[0], int(res in dc[1]))
                q = sum(M[i][j] for i in range(1, 9) for j in range(1, 9)); bt = hg > 0 and ag > 0; pb = CA.p('BTTS', q); pend.append(('BTTS', q, bt))
                E.add('BTTS', 'Gol', 'Goal / No Goal', lab, max(pb, 1 - pb), int(bt if pb >= 0.5 else not bt))
                ex = max(((M[i][j], i, j) for i in range(6) for j in range(6)))
                E.add('ESATTO', 'Esatto', 'Risultato esatto (più probabile)', lab, max(0.5, ex[0]), int(ex[1] == hg and ex[2] == ag))
                top3 = sorted(((M[i][j], i, j) for i in range(6) for j in range(6)), reverse=True)[:3]
                E.add('ESATTO3', 'Esatto', 'Risultato esatto (uno dei 3 più probabili)', lab, max(0.5, sum(x[0] for x in top3)), int(any(x[1] == hg and x[2] == ag for x in top3)))
                ah = num(r.get('AHh'))
                if ah is not None:
                    # linea asiatica di casa: vince se hg + ah > ag (mezza linea), pareggio = rimborso escluso
                    pw = sum(M[i][j] for i in range(9) for j in range(9) if i + ah > j); pl = sum(M[i][j] for i in range(9) for j in range(9) if i + ah < j)
                    if hg + ah != ag and pw + pl > 0:
                        w = pw / (pw + pl); side = w >= 0.5; hit = int((hg + ah > ag) == side)
                        E.add('AH', 'Handicap', 'Handicap asiatico (linea del mercato)', lab, max(w, 1 - w), hit)
            if 'g1' in exp and 'g' in exp:
                # tempo con più gol
                g1 = val['g1'][0] + val['g1'][1]; g2 = val['g'][0] + val['g'][1] - g1
                e1 = sum(exp['g1']); e2 = sum(exp['g']) - e1
                p1 = sum(pois(e1, a) * pois(e2, b) for a in range(10) for b in range(10) if a > b); p2 = sum(pois(e1, a) * pois(e2, b) for a in range(10) for b in range(10) if b > a); pX = 1 - p1 - p2
                best = max((p1, 1), (p2, 2), (pX, 0)); out = 1 if g1 > g2 else (2 if g2 > g1 else 0)
                E.add('TEMPO_GOL', 'Gol 1° tempo', 'Tempo con più gol', lab, best[0], int(best[1] == out))
                h2 = max(0.5, 1 - math.exp(-e2)); E.add('G2T_O05', 'Gol 1° tempo', 'Secondo tempo Over 0,5', lab, max(1 - math.exp(-e2), math.exp(-e2)), int((g2 > 0) == (1 - math.exp(-e2) >= 0.5)))
            if 'r' in exp:
                er = sum(exp['r']); p = 1 - math.exp(-er); o = val['r'][0] + val['r'][1] > 0
                E.add('ROSSO', 'Rossi', 'Espulsione nella partita Sì/No', lab, max(p, 1 - p), int(o == (p >= 0.5)))
        # aggiorna dopo il pronostico
        for kb, q, o in pend: CA.upd(kb, q, o)
        pend = []
        for st, (vh, va) in val.items():
            if vh is None or va is None: continue
            x = LL.setdefault(st, [0, 0.0, 0.0, 0.0]); x[0] += 1; x[1] += vh; x[2] += va; x[3] += (vh + va) ** 2
            T.add('h', st, vh, va); U.add('a', st, va, vh)
        ref = (r.get('Referee') or '').strip()
        if ref and val['y'][0] is not None:
            rf = refs.setdefault(ref, [0, 0.0, 0.0, lab]); rf[0] += 1; rf[1] += val['y'][0] + val['y'][1]; rf[2] += (val['r'][0] or 0) + (val['r'][1] or 0)
        # a fine 2025-26 le medie diventano il punto di partenza (peso 6 partite) per il 2026-27
        if ss == '2526':
            for st in STATS:
                for side, tt, nm in (('h', T, ht), ('a', U, at)):
                    d = tt.h if side == 'h' else tt.a; x = d.get(st)
                    if x and x[0]: prev[(lg, nm, st, side)] = (x[1] / x[0], x[2] / x[0], min(6.0, x[0] / 2))
    # ---- uscita ----
    def fin(x):
        n = x['n']
        o = {'fam': x['fam'], 'label': x['label'], 'n': n, 'acc': round(x['hit'] / n, 4) if n else None, 'p': round(x['sp'] / n, 4) if n else None,
             'brier': round(x['br'] / n, 4) if n else None, 'sol_n': x['sol_n'], 'sol_acc': round(x['sol_hit'] / x['sol_n'], 4) if x['sol_n'] else None,
             'bins': [[b[0], round(b[1] / b[0], 3) if b[0] else None, round(b[2] / b[0], 3) if b[0] else None] for b in x['bins']]}
        if x['mk_n']: o['mk'] = {'n': x['mk_n'], 'brier_mercato': round(x['mk_br'] / x['mk_n'], 4), 'brier_modello': round(x['mo_br'] / x['mk_n'], 4)}
        return o
    ev = {}; evl = {}
    for k, x in E.m.items():
        if '@' in k:
            a, b = k.split('@', 1)
            if x['n'] >= 15: evl.setdefault(b, {})[a] = fin(x)
        else:
            ev[k] = fin(x)
    # medie di squadra correnti (stagione più recente disponibile per squadra)
    tout = {}
    for (lg, ss, nm), T in teams.items():
        if ss != SEASONS[-1] and (lg, SEASONS[-1], nm) in teams: continue
        o = {'lg': LEAGUES[lg], 'ss': ss}
        for st in STATS:
            a = T.h.get(st, [0, 0, 0]); b = T.a.get(st, [0, 0, 0]); n = a[0] + b[0]
            if n: o[st] = [n, round((a[1] + b[1]) / n, 2), round((a[2] + b[2]) / n, 2), a[0], round(a[1] / a[0], 2) if a[0] else None, round(a[2] / a[0], 2) if a[0] else None, b[0], round(b[1] / b[0], 2) if b[0] else None, round(b[2] / b[0], 2) if b[0] else None]
        tout[nm] = o
    lout = {}
    for (lg, ss), LL in L.items():
        if ss != SEASONS[-1]: continue
        lout[LEAGUES[lg]] = {st: [x[0], round(x[1] / x[0], 3), round(x[2] / x[0], 3)] for st, x in LL.items() if x[0]}
    rout = {k: [v[0], round(v[1] / v[0], 2), round(v[2] / v[0], 2), v[3]] for k, v in refs.items() if v[0] >= 3}
    out = {'t': int(time.time() * 1000), 'fonte': 'football-data.co.uk (statistiche ufficiali partita per partita)', 'partite': len(rows),
           'stagioni': SEASONS, 'campionati': list(LEAGUES.values()), 'disp': {k: (round(v, 2) if v < 1e8 else None) for k, v in disp.items()},
           'eval': ev, 'evalLg': evl, 'cal': CA.t, 'teams': tout, 'leagues': lout, 'refs': rout}
    os.makedirs(os.path.join(ROOT, 'state'), exist_ok=True)
    s = json.dumps(out, separators=(',', ':'), ensure_ascii=False)
    open(os.path.join(ROOT, 'state', 'markets.json'), 'w').write(s)
    print('mercati verificati:', len(ev), '· squadre:', len(tout), '· arbitri:', len(rout), '· byte:', len(s))
    return out


if __name__ == '__main__':
    o = run(sys.argv[1] if len(sys.argv) > 1 else None)
    top = sorted(o['eval'].items(), key=lambda kv: -kv[1]['n'])
    for k, x in top[:200]:
        if x['n'] >= 300: print('%-14s %-48s n=%5d acc=%.3f p=%.3f brier=%.3f sol=%s/%s %s' % (k, x['label'], x['n'], x['acc'], x['p'], x['brier'], x['sol_n'], x['sol_acc'], x.get('mk', '')))
