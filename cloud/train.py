#!/usr/bin/env python3
"""Addestramento continuo nel cloud di Pronostici Pro.
Apre l'app (index.html del repository) in un browser senza schermo, carica il modello addestrato
dell'ultimo giro (state/state.json), lavora per circa MINUTI minuti e salva il nuovo modello:
- tutte le partite della stagione dei campionati principali (giocatori, falli, cartellini, xG, classifiche)
- pronostici pre-partita registrati per le partite delle prossime ore (cosi' poi si possono verificare)
- formazioni ufficiali per le partite imminenti, con ammoniti e marcatori ricalcolati
- verifica di ogni partita finita con correzione automatica (taratura, attacco/difesa squadre)
- storico ESPN sempre piu' profondo
Uso: python3 cloud/train.py [MINUTI]
"""
import asyncio, json, os, sys, time
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN = float(sys.argv[1]) if len(sys.argv) > 1 else 20
OK = ['www.olbg.com', 'webws.365scores.com', 'site.api.espn.com', 'www.fotmob.com', 'site.web.api.espn.com', 'sports.core.api.espn.com', 'prod-cdn-public-api.livescore.com', 'www.transfermarkt.it', 'news.google.com', 'www.youtube.com']
# siti che rispondono solo a un browser vero (pagina con JavaScript), non a curl: si aprono con Chromium attraverso il proxy
REAL = ['www.mondopengwin.it']
LOCAL = ['wt', 'lsOut', 'settings', 'log', 'yt', 'tg', 'sofaSt', 'olbg', 'luT', 'luSt', 'store', 'cloud']

def phone_slim(S):
    """Solo cio' che serve al telefono: modello addestrato completo (taratura, Elo, statistiche squadre e giocatori),
    partite di oggi e dei prossimi giorni, verifiche recenti. Lo storico grezzo resta nel cloud."""
    import datetime as _dt
    now = time.time() * 1000
    def kt(x):
        try: return _dt.datetime.fromisoformat(str(x.get('kick')).replace('Z', '+00:00')).timestamp() * 1000
        except Exception: return 0
    O = dict(S)
    for k in ('seen', 'tcSeen', 'fmSeen', 'resolvedIds', 'fmIng', 'preLam'): O.pop(k, None)
    keep = lambda o, h: {i: v for i, v in (o or {}).items() if isinstance(v, dict) and (not kt(v) or kt(v) > now - h * 3600e3)}
    fut = lambda o, h, ah: {i: v for i, v in (o or {}).items() if isinstance(v, dict) and (not kt(v) or (now - h * 3600e3 < kt(v) < now + ah * 3600e3))}
    O['snap'] = fut(S.get('snap'), 24, 30); O['snapPre'] = fut(S.get('snapPre'), 24, 30)
    O['pd'] = fut(S.get('pd'), 6, 30); O['pps'] = keep(S.get('pps'), 24); O['apk'] = keep(S.get('apk'), 24)
    O.pop('picks', None)  # le registrazioni da verificare le verifica il cloud
    ids = set(O['snap'])
    for k in ('xi', 'cp', 'tipA', 'news', 'refOf'): O[k] = {i: v for i, v in (S.get(k) or {}).items() if i in ids}
    V = S.get('ver') or {}; O['ver'] = dict(sorted(V.items(), key=lambda x: -(x[1].get('t') or 0) if isinstance(x[1], dict) else 0)[:250])
    O['audits'] = (S.get('audits') or [])[:60]
    O['players'] = {k: v for k, v in (S.get('players') or {}).items() if isinstance(v, list) and (v[0] or 0) >= 3}
    O['fmP'] = {k: v for k, v in (S.get('fmP') or {}).items() if isinstance(v, dict) and now - (v.get('t') or 0) < 864e5}
    O['lamPre'] = {k: v for k, v in (S.get('lamPre') or {}).items() if isinstance(v, list) and now - (v[3] if len(v) > 3 else v[2]) < 2 * 864e5}
    return json.dumps(O, separators=(',', ':'))

async def main():
    t0 = time.time(); st_path = os.path.join(ROOT, 'state', 'state.json')
    print('0. tutti i mercati dei bookmaker (statistiche ufficiali football-data.co.uk)')
    mk = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import markets
        mk = markets.run()['t']
    except Exception as e:
        print('   mercati non aggiornati:', e)
        try: mk = json.load(open(os.path.join(ROOT, 'state', 'markets.json')))['t']
        except Exception: mk = None
    prev = open(st_path).read() if os.path.exists(st_path) else 'null'
    # CORREZIONE UNA TANTUM (28/11): dal 23/11 la taratura riceveva registrazioni fatte con gol attesi ricalcolati DOPO il risultato
    # (favorita indovinata 83-97% contro 75% vero). Si tolgono quelle registrazioni; da ora si registra solo ciò che era scritto prima del via.
    try:
        fxp = os.path.join(ROOT, 'data', 'fix', 'leak_2026-11-28.json')
        if prev != 'null' and os.path.exists(fxp):
            SS = json.loads(prev)
            if not SS.get('fixLeak1'):
                FX = json.load(open(fxp)); nk = 0
                for k, d in FX['tracker'].items():
                    t = (SS.get('tracker') or {}).get(k)
                    if not t or t.get('n', 0) <= d['n']: continue
                    for f in ('n', 'hits', 'sumP', 'br'): t[f] = max(0, (t.get(f) or 0) - d.get(f, 0))
                    for f in ('bd', 'hb'):
                        if d.get(f) and t.get(f): t[f] = [[max(0, t[f][i][j] - d[f][i][j]) for j in range(3)] for i in range(len(t[f]))]
                    nk += 1
                for lg, m in FX['ctr'].items():
                    for key, dv in m.items():
                        v = ((SS.get('ctr') or {}).get(lg) or {}).get(key)
                        if v and v[0] > dv[0]: SS['ctr'][lg][key] = [v[0] - dv[0], v[1] - dv[1], v[2] - dv[2]]
                SS['fixLeak1'] = 1; prev = json.dumps(SS); print('   correzione taratura contaminata: tolte le registrazioni dal 23/11 su', nk, 'mercati')
            del SS
    except Exception as e: print('   correzione non applicata:', e)
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        rb = await p.chromium.launch(proxy={'server': os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or 'http://127.0.0.1:36429'}, args=['--disable-blink-features=AutomationControlled'])
        rbc = await rb.new_context(user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Mobile Safari/537.36', locale='it-IT')
        async def real(u):
            q = await rbc.new_page()
            try:
                await q.goto(u, timeout=45000); await q.wait_for_timeout(6000); return (await q.content()).encode('utf-8')
            finally: await q.close()
        H = {'access-control-allow-origin': '*', 'content-type': 'application/json'}
        async def route(r):
            u = r.request.url
            if u.startswith('file:'): return await r.continue_()
            if any(h in u for h in REAL):
                try: return await r.fulfill(status=200, body=await real(u), headers={'access-control-allow-origin': '*', 'content-type': 'text/html; charset=utf-8'})
                except Exception: return await r.abort()
            if not any(h in u for h in OK): return await r.abort()
            pr = await asyncio.create_subprocess_exec('curl', '-sS', '--compressed', '-m', '45', '-A', 'Mozilla/5.0 (Linux; Android 13) Chrome/120 Mobile', u, stdout=asyncio.subprocess.PIPE)
            out, _ = await pr.communicate(); await r.fulfill(status=200, body=out, headers=H)
        await pg.route('**/*', route)
        await pg.add_init_script('window.__CLOUD=true; window.__PRELOAD_S=' + prev + ';')
        await pg.goto('file://' + os.path.join(ROOT, 'index.html')); await pg.wait_for_timeout(4000)
        await pg.evaluate("()=>{const s=window.__S();s.settings=s.settings||{};s.settings.updUrl='https://127.0.0.1/none';s.cloud={chk:Date.now()+9e12}}")
        left = lambda: MIN * 60 - (time.time() - t0)
        SNAPN = "(()=>{const S=window.__S();return 'pronostici in archivio '+Object.keys(S.snap||{}).length+', verificati '+Object.keys(S.ver||{}).length})()"
        async def ev(js, tmo=600):
            try: return await asyncio.wait_for(pg.evaluate(js), tmo)
            except Exception as e: print('  !', str(e)[:160]); return None
        print('1. campionati principali'); 
        for _ in range(40):
            if left() < MIN * 60 * 0.75: break
            n = await ev("async()=>await window.__T.leagueStep(25)", 300)
            if not n: break
        # formazioni ufficiali in continuo per tutto il giro (escono circa 60' prima: un giro ogni ora le prende tutte prima del via)
        stop = {'v': False}
        async def lu_loop():
            while not stop['v']:
                await ev("async()=>{await window.__T.pollLU(); return 1}", 240)
                for _ in range(18):
                    if stop['v']: break
                    await asyncio.sleep(5)
        lu_task = asyncio.create_task(lu_loop())
        print('2. palinsesto completo di oggi, domani e dopodomani: pre-pronostico di ogni partita, poi analisi profonda finché c\'è tempo')
        print('  ', await ev("async()=>JSON.stringify(await window.__T.palinsestoStep([0,1,2], %d))" % int(MIN * 60 * 1000 * 0.35), 1800))
        print('   ', await ev(SNAPN))
        print('2b. tipster (OLBG e voti/quote 365Scores) sulle partite delle prossime 48 ore')
        print('  ', await ev("""async()=>{const T=window.__T,S=window.__S(); let L=T.getEvents().slice(); try{L=L.concat(await T.majorsAhead())}catch(e){} const seen={}; L=L.filter(e=>!e.done&&(seen[e.id]?0:(seen[e.id]=1)));
          const n=await T.taStep(120,L); const o=(S.tsrc||{}).OLBG; return n+' partite con voti/quote; OLBG '+(o?(o.ok?o.list.length+' consigli':'errore '+o.err):'-')}""", 900))
        print('   ', await ev(SNAPN))
        print('2c. Tipzone_TV (video: elenco, descrizioni, sottotitoli quando YouTube li concede) e pagine web dei tipster (MondoPengwin) con browser vero')
        print('  ', await ev("async()=>{const n=await window.__T.ytStep(true); const Y=window.__S().yt||{}, w=Y.w||{}, V=Y.v||{}; const vs=Object.keys(V).map(id=>(V[id].title||id).slice(0,38)+': '+(V[id].tr?'sottotitoli':'descrizione')+' '+(V[id].m||[]).length+' partite'+(V[id].why?' ('+V[id].why+')':'')).join(' | '); return n+' pagine lette; '+Object.keys(w).map(u=>u.replace(/https?:\\/\\/(www\\.)?/,'').slice(0,40)+' '+(w[u].ok?'ok '+(w[u].m||[]).length+' partite':'no '+(w[u].why||''))).join(' | ')+' || VIDEO: '+vs}", 600))
        print('  infortunati Transfermarkt:', await ev("async()=>{await window.__T.siteStep(); const I=window.__S().tmInj||{}; return Object.keys(I).map(k=>k+' '+((I[k].L||[]).length)).join(', ')}", 300))
        print('   ', await ev(SNAPN))
        print('3. formazioni ufficiali'); print('  ', await ev("async()=>{await window.__T.pollLU(); return Object.keys(window.__S().lu||{}).length}", 300))
        print('   ', await ev(SNAPN))
        print('4. verifica e audit di tutte le partite finite (ieri l\'altro, ieri, oggi), prima e dopo le ufficiali')
        r = await ev("""async()=>{const T=window.__T,S=window.__S(); const LL=[]; let L=[]; for(const k of [0,-1,-2]){try{const d=await T.dayEvents(new Date(Date.now()+k*86400e3)); LL.push(d); L=L.concat(d)}catch(e){}}
          const F=L.filter(e=>e.done&&S.snap&&S.snap[e.id]&&!(S.ver&&S.ver[e.id])); let n=0, t0=Date.now(); let i=0;
          await Promise.all([0,1,2,3].map(async()=>{while(i<F.length&&Date.now()-t0<%d){const e=F[i++];try{T.prepEv(e);await T.verifyMatch(e);n++}catch(x){}}}));
          const C=T.covStep(LL); const ds=Object.keys(C).sort().slice(-3); return n+' verificate su '+F.length+' · copertura '+ds.map(d=>d+': '+JSON.stringify(C[d])).join(' | ')}""" % int(MIN * 60 * 1000 * 0.25), 1500)
        print('  ', r)
        print('   ', await ev(SNAPN))
        print('4b. ripasso stagioni 2025-26 e 2026-27 (pre-pronostico e confronto)')
        t1=time.time()
        while left() > MIN*60*0.25 and time.time()-t1 < MIN*60*0.35:
            n = await ev("async()=>await window.__T.replayStep(10)", 600)
            if not n: break
        print('  ', await ev("JSON.stringify({giorno:(window.__S().rp||{}).day, partite:(window.__S().rp||{}).n})"))
        print('   ', await ev(SNAPN))
        print('5. storico')
        while left() > 90:
            await ev("async()=>{await window.__T.histStep()}", 300)
            await ev("async()=>await window.__T.leagueStep(25)", 300)
        print('   ', await ev(SNAPN))
        stop['v'] = True
        try: await asyncio.wait_for(lu_task, 300)
        except Exception: pass
        print('  formazioni ufficiali prese in questo giro:', await ev("Object.keys(window.__S().lu||{}).length"))
        out = await pg.evaluate("""(L)=>{const S=window.__S(),o={};Object.keys(S).forEach(k=>{if(L.indexOf(k)<0)o[k]=S[k]}); if(S.yt&&S.yt.w)o.ytw=S.yt.w; if(S.yt&&S.yt.v)o.ytv=S.yt.v;
          // archivi per id: solo gli ultimi 10 giorni
          const cut=Date.now()-10*864e5, cut2=Date.now()-36*3600e3, V=S.ver||{}; ['snap','snapPre'].forEach(k=>{if(o[k]){const x={};Object.keys(o[k]).forEach(id=>{const v=o[k][id];if(!v||!v.kick)return; const kt=new Date(v.kick); if(kt>cut&&(!V[id]||kt>cut2))x[id]=v});o[k]=x}});
          return JSON.stringify(o)}""", LOCAL)
        score = await pg.evaluate("Object.values(window.__S().tracker||{}).reduce((a,t)=>a+(t.n||0),0)")
        nver = await pg.evaluate("Object.keys(window.__S().ver||{}).length")
        await b.close(); await rb.close()
    os.makedirs(os.path.join(ROOT, 'state'), exist_ok=True)
    # consegne di Claude (data/consegne): audit automatico il giorno dopo e risultati per tipo nello stato dell'app
    try:
        import glob, subprocess as sp, datetime as dt
        oo = json.loads(out); C = oo.get('consegne') or {}
        for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'consegne', '????-??-??.json'))):
            day = os.path.basename(f)[:10]; fe = f.replace('.json', '_esito.json')
            if not os.path.exists(fe) and day < dt.date.today().isoformat():
                sp.run([sys.executable, os.path.join(ROOT, 'cloud', 'audit_consegne.py'), f], timeout=300)
            if os.path.exists(fe): C[day] = json.load(open(fe))
        if C: oo['consegne'] = C; out = json.dumps(oo)
    except Exception as e: print('   consegne non lette:', e)
    open(st_path, 'w').write(out)
    # VERSIONE LEGGERA PER IL TELEFONO (28/11): 36 MB rendevano l'app lenta; il telefono riceve solo cio' che gli serve
    ph = None
    try:
        ph = phone_slim(json.loads(out)); open(os.path.join(ROOT, 'state', 'phone.json'), 'w').write(ph)
    except Exception as e: print('   versione telefono non creata:', e)
    meta = {'t': int(time.time() * 1000), 'score': score, 'verificate': nver, 'size': len(out), 'ph': len(ph) if ph else 0, 'minuti': round((time.time() - t0) / 60, 1), 'mk': mk}
    open(os.path.join(ROOT, 'state', 'meta.json'), 'w').write(json.dumps(meta))
    print('FATTO', json.dumps(meta))

asyncio.run(main())
