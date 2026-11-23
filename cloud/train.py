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
OK = ['www.olbg.com', 'webws.365scores.com', 'site.api.espn.com', 'www.fotmob.com', 'site.web.api.espn.com', 'sports.core.api.espn.com']
LOCAL = ['settings', 'log', 'yt', 'tg', 'sofaSt', 'olbg', 'luT', 'luSt', 'store', 'cloud']

async def main():
    t0 = time.time(); st_path = os.path.join(ROOT, 'state', 'state.json')
    prev = open(st_path).read() if os.path.exists(st_path) else 'null'
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        H = {'access-control-allow-origin': '*', 'content-type': 'application/json'}
        async def route(r):
            u = r.request.url
            if u.startswith('file:'): return await r.continue_()
            if not any(h in u for h in OK): return await r.abort()
            pr = await asyncio.create_subprocess_exec('curl', '-sS', '--compressed', '-m', '45', '-A', 'Mozilla/5.0 (Linux; Android 13) Chrome/120 Mobile', u, stdout=asyncio.subprocess.PIPE)
            out, _ = await pr.communicate(); await r.fulfill(status=200, body=out, headers=H)
        await pg.route('**/*', route)
        await pg.add_init_script('window.__CLOUD=true; window.__PRELOAD_S=' + prev + ';')
        await pg.goto('file://' + os.path.join(ROOT, 'index.html')); await pg.wait_for_timeout(4000)
        await pg.evaluate("()=>{const s=window.__S();s.settings=s.settings||{};s.settings.updUrl='https://127.0.0.1/none';s.cloud={chk:Date.now()+9e12}}")
        left = lambda: MIN * 60 - (time.time() - t0)
        async def ev(js, tmo=600):
            try: return await asyncio.wait_for(pg.evaluate(js), tmo)
            except Exception as e: print('  !', str(e)[:160]); return None
        print('1. campionati principali'); 
        for _ in range(40):
            if left() < MIN * 60 * 0.65: break
            n = await ev("async()=>await window.__T.leagueStep(25)", 300)
            if not n: break
        print('2. palinsesto e pronostici pre-partita')
        r = await ev("""async()=>{const T=window.__T; await T.loadDay(true); let L=T.getEvents().slice(); try{L=L.concat(await T.majorsAhead())}catch(e){}
          const now=Date.now(), seen={}; L=L.filter(e=>!e.done&&e.state==='pre'&&new Date(e.date)>now&&new Date(e.date)-now<30*3600e3&&(seen[e.id]?0:(seen[e.id]=1)));
          L.sort((a,b)=>(/^(ita|eng|esp|ger|fra|por|ned)\\.|^uefa\\./.test(b.league||'')-/^(ita|eng|esp|ger|fra|por|ned)\\.|^uefa\\./.test(a.league||''))||new Date(a.date)-new Date(b.date)); L=L.slice(0,160);
          let i=0,n=0; await Promise.all([0,1,2,3].map(async()=>{while(i<L.length){const e=L[i++];try{T.prepEv(e);await T.analyzeMatch(e);await T.refreshSnap(e);n++}catch(x){}}})); return n+' su '+L.length}""", 900)
        print('  analizzate', r)
        print('2b. tipster (OLBG e voti/quote 365Scores) sulle partite delle prossime 48 ore')
        print('  ', await ev("""async()=>{const T=window.__T,S=window.__S(); let L=T.getEvents().slice(); try{L=L.concat(await T.majorsAhead())}catch(e){} const seen={}; L=L.filter(e=>!e.done&&(seen[e.id]?0:(seen[e.id]=1)));
          const n=await T.taStep(120,L); const o=(S.tsrc||{}).OLBG; return n+' partite con voti/quote; OLBG '+(o?(o.ok?o.list.length+' consigli':'errore '+o.err):'-')}""", 900))
        print('3. formazioni ufficiali'); print('  ', await ev("async()=>{await window.__T.pollLU(); return Object.keys(window.__S().lu||{}).length}", 300))
        print('4. verifica partite finite')
        r = await ev("""async()=>{const T=window.__T,S=window.__S(); let L=[]; for(const k of [0,-1]){try{L=L.concat(await T.dayEvents(new Date(Date.now()+k*86400e3)))}catch(e){}}
          const F=L.filter(e=>e.done&&S.snap&&S.snap[e.id]&&!(S.ver&&S.ver[e.id])); let n=0; for(const e of F){try{T.prepEv(e);await T.verifyMatch(e);n++}catch(x){}} return n+' verificate su '+F.length}""", 900)
        print('  ', r)
        print('5. storico')
        while left() > 90:
            await ev("async()=>{await window.__T.histStep()}", 300)
            await ev("async()=>await window.__T.leagueStep(25)", 300)
        out = await pg.evaluate("""(L)=>{const S=window.__S(),o={};Object.keys(S).forEach(k=>{if(L.indexOf(k)<0)o[k]=S[k]});
          // archivi per id: solo gli ultimi 10 giorni
          const cut=Date.now()-10*864e5; ['snap','snapPre'].forEach(k=>{if(o[k]){const x={};Object.keys(o[k]).forEach(id=>{const v=o[k][id];if(!v||!v.kick||new Date(v.kick)>cut)x[id]=v});o[k]=x}});
          return JSON.stringify(o)}""", LOCAL)
        score = await pg.evaluate("Object.values(window.__S().tracker||{}).reduce((a,t)=>a+(t.n||0),0)")
        nver = await pg.evaluate("Object.keys(window.__S().ver||{}).length")
        await b.close()
    os.makedirs(os.path.join(ROOT, 'state'), exist_ok=True)
    open(st_path, 'w').write(out)
    meta = {'t': int(time.time() * 1000), 'score': score, 'verificate': nver, 'size': len(out), 'minuti': round((time.time() - t0) / 60, 1)}
    open(os.path.join(ROOT, 'state', 'meta.json'), 'w').write(json.dumps(meta))
    print('FATTO', json.dumps(meta))

asyncio.run(main())
