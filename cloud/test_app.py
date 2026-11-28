import asyncio, json, time, sys
from playwright.async_api import async_playwright
APP='file:///home/claude/pronostici/index.html'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':390,'height':844})
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        H={'access-control-allow-origin':'*','content-type':'application/json'}
        OK=['webws.365scores.com','site.api.espn.com','www.fotmob.com','www.olbg.com','raw.githubusercontent.com']
        async def route(r):
            u=r.request.url
            if u.startswith('file:'): return await r.continue_()
            if not any(h in u for h in OK): return await r.abort()
            pr=await asyncio.create_subprocess_exec('curl','-sS','--compressed','-m','45','-A','Mozilla/5.0 (Linux; Android 13) Chrome/120 Mobile',u,stdout=asyncio.subprocess.PIPE); out,_=await pr.communicate()
            await r.fulfill(status=200,body=out,headers=H)
        await pg.route('**/*',route)
        res=[]
        def rep(name,ok,det=''): res.append((name,ok,det)); print(('OK  ' if ok else 'ERR ')+name+(' — '+det if det else ''),flush=True)
        t0=time.time(); await pg.goto(APP); await pg.wait_for_timeout(5000)
        rep('avvio',True,'%.1fs'%(time.time()-t0))
        async def tab(t,sel,wait=6000,must=None):
            n0=len(errs); t1=time.time()
            try:
                await pg.click('nav button[data-t=%s]'%t); await pg.wait_for_timeout(wait); txt=await pg.inner_text('#app')
                ok=(must is None or must.lower() in txt.lower()) and len(errs)==n0
                rep('scheda '+sel,ok,'%.1fs, %d caratteri%s'%(time.time()-t1,len(txt),(' · errori: '+'; '.join(errs[n0:])) if len(errs)>n0 else ''))
                return txt
            except Exception as e: rep('scheda '+sel,False,str(e)[:150]); return ''
        await tab('quadro','Quadro',20000,'Campionati maggiori')
        await tab('oggi','Partite',8000)
        await tab('live','Live',12000,'in corso')
        await tab('prec','Precisione',4000)
        await tab('multi','Multipla',2000,'Costruisci')
        # multipla: mercati e esatti
        for tipo,q in [('m','20'),('m','all'),('m','50'),('e','50')]:
            n0=len(errs); t1=time.time()
            try:
                await pg.click('nav button[data-t=multi]'); await pg.wait_for_timeout(1500)
                await pg.select_option('#md',tipo); await pg.select_option('#tq',q); await pg.click('#go')
                txt=''
                for k in range(90):
                    await pg.wait_for_timeout(2000); txt=await pg.inner_text('#mm')
                    if 'entrano tutte' in txt.lower() or 'nessun' in txt.lower(): break
                rep('multipla %s quota %s'%('mercati' if tipo=='m' else 'esatti',q),'entrano tutte' in txt.lower() and len(errs)==n0,'%.0fs %s'%(time.time()-t1,'; '.join(errs[n0:])))
            except Exception as e: rep('multipla '+tipo+q,False,str(e)[:150])
        # pagine di Altro
        for go,name in [('tip','Tipster'),('err','Errori e correzioni'),('tr','Addestramento'),('metodo','Metodo'),('arb','Arbitri'),('cerca','Cerca'),('fonti','Fonti'),('upd','Aggiorna'),('rap','Rapporto'),('imp','Impostazioni')]:
            n0=len(errs)
            try:
                await pg.click('nav button[data-t=altro]'); await pg.wait_for_timeout(600); el=await pg.query_selector('[data-go=%s]'%go)
                if not el: rep('Altro → '+name,False,'voce mancante'); continue
                await el.click(); await pg.wait_for_timeout(5000); txt=await pg.inner_text('#app')
                rep('Altro → '+name,len(errs)==n0 and len(txt)>100,'%d caratteri %s'%(len(txt),'; '.join(errs[n0:])))
            except Exception as e: rep('Altro → '+name,False,str(e)[:150])
        # partita: tutte le sezioni
        n0=len(errs)
        try:
            ev=await pg.evaluate("""async()=>{const T=window.__T;const L=await T.dayEvents(new Date());const e=L.find(x=>!x.done&&x.state==='pre'&&/^(ita|eng|esp|ger|fra)\\.1/.test(x.league||''))||L.find(x=>!x.done&&x.state==='pre');return e?{id:e.id,n:e.home+' - '+e.away}:null}""")
            if not ev:
                ev=await pg.evaluate("""async()=>{const T=window.__T;const L=await T.dayEvents(new Date(Date.now()+86400e3));const e=L.find(x=>/^(ita|eng|esp|ger|fra)\\.1/.test(x.league||''))||L[0];return {id:e.id,n:e.home+' - '+e.away,d:1}}""")
            await pg.evaluate("""async(o)=>{const T=window.__T;const L=await T.dayEvents(new Date(Date.now()+(o.d?86400e3:0)));const e=L.find(x=>x.id===o.id);T.prepEv(e);T.openMatch(e)}""",ev)
            await pg.wait_for_timeout(16000)
            secs=await pg.evaluate("Array.from(document.querySelectorAll('#mt .seg button')).map(b=>b.dataset.s)")
            bad=[]
            for s in secs:
                await pg.click('#mt .seg button[data-s=%s]'%s); await pg.wait_for_timeout(500)
                t=await pg.evaluate("(s)=>{const p=document.querySelector('#mt .pane[data-p='+s+']');return p?p.innerText:''}",s)
                if len(t)<40 or 'undefined' in t or 'NaN' in t: bad.append(s+'('+str(len(t))+(' undefined' if 'undefined' in t else '')+(' NaN' if 'NaN' in t else '')+')')
            rep('partita '+ev['n']+': sezioni '+','.join(secs),not bad and len(errs)==n0,'problemi: '+', '.join(bad)+' '+'; '.join(errs[n0:]) if bad or len(errs)>n0 else '')
        except Exception as e: rep('partita',False,str(e)[:200])
        # live: apri la prima partita in corso
        n0=len(errs)
        try:
            await pg.click('nav button[data-t=live]'); await pg.wait_for_timeout(9000)
            cs=await pg.query_selector_all('.lvc')
            if cs:
                nm=(await cs[0].inner_text()).replace('\n',' ')[:60]; t1=time.time(); await cs[0].click()
                for k in range(30):
                    if await pg.query_selector('#ctab'): break
                    await pg.wait_for_timeout(500)
                topen=time.time()-t1; tabs=await pg.evaluate("Array.from(document.querySelectorAll('#ctab button')).map(b=>b.dataset.c)")
                bad=[]
                for c in tabs:
                    await pg.click('#ctab button[data-c=%s]'%c); await pg.wait_for_timeout(1200); t=await pg.inner_text('#cbody')
                    if 'undefined' in t or 'NaN' in t: bad.append(c)
                rep('live: '+nm+' aperta in %.1fs, schede '%(topen)+','.join(tabs),bool(tabs) and not bad and len(errs)==n0,('problemi '+','.join(bad)+' '+'; '.join(errs[n0:])) if bad or len(errs)>n0 else '')
            else: rep('live: nessuna partita in corso',True)
        except Exception as e: rep('live centro',False,str(e)[:200])
        # ADDESTRAMENTO PULITO (28/11): mai imparare da gol attesi ricalcolati dopo il risultato; guardia che si blocca da sola
        try:
            r = await pg.evaluate("""()=>{const T=window.__T,S=window.__S(),k='FAV_NOLOSE',n=()=>((S.tracker||{})[k]||{}).n||0,kick=new Date(Date.now()-864e5).toISOString();
              const mk=id=>({id,league:'ita.1',home:'Internazionale',away:'Genoa',date:kick,done:true,state:'post',hs:2,as:0});
              const g0=S.guard; delete S.guard; const a0=n(); T.learnEvent(mk('TSTLEAK1'),null); const a1=n();
              S.lamPre=S.lamPre||{}; S.lamPre['TSTLEAK2']=[1.6,0.9,Date.now()-30*3600e3,new Date(kick).getTime()]; T.learnEvent(mk('TSTLEAK2'),null); const a2=n();
              const now=Date.now(),v={}; ['FAV_NOLOSE','FAV_WIN','FAV_SEGNA','OVER25','UNDER35','EX3'].forEach(q=>{const t=S.tracker[q]||{n:0,hits:0,sumP:0},b=S.tracker['PRE_'+q]||{n:0,hits:0,sumP:0}; v[q]=[(t.n||0)-400,(t.hits||0)-400*0.95,(t.sumP||0)-400*0.80,b.n||0,b.hits||0,b.sumP||0];});
              S.guard={h:[{t:now-21*3600e3,v}]}; const G=T.guardStep(); S.lamPre['TSTLEAK3']=[1.6,0.9,Date.now()-30*3600e3,new Date(kick).getTime()]; T.learnEvent(mk('TSTLEAK3'),null); const a3=n();
              const blocked=!!(S.guard&&S.guard.block); if(g0) S.guard=g0; else delete S.guard; ['TSTLEAK1','TSTLEAK2','TSTLEAK3'].forEach(id=>{delete S.lamPre[id]; if(S.seen) delete S.seen[id]; if(S.snap) delete S.snap[id];});
              return {senza_pre:a1-a0, con_pre:a2-a1, bloccata:blocked, dopo_blocco:a3-a2, bad:G.bad}}""")
            ok = r['senza_pre']==0 and r['con_pre']==1 and r['bloccata'] and r['dopo_blocco']==0
            rep('addestramento pulito e guardia automatica', ok, json.dumps(r))
        except Exception as e: rep('addestramento pulito e guardia automatica', False, str(e)[:200])
        # tasto indietro
        try:
            await pg.go_back(); await pg.wait_for_timeout(1500); rep('tasto indietro',True,(await pg.inner_text('#app'))[:40].replace('\n',' '))
        except Exception as e: rep('tasto indietro',False,str(e)[:100])
        logs=await pg.evaluate("(window.__S().log||[]).filter(x=>/errore|error|TypeError|undefined|Cannot/i.test(x)).slice(-15)")
        print('LOG ERRORI APP:',json.dumps(logs,ensure_ascii=False)[:3000])
        print('TOTALE: %d ok, %d errori'%(sum(1 for r in res if r[1]),sum(1 for r in res if not r[1])))
        await b.close()
asyncio.run(main())
