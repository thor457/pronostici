import asyncio, json, time
from playwright.async_api import async_playwright
APP='file:///home/claude/pronostici/index.html'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':390,'height':844})
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        H={'access-control-allow-origin':'*','content-type':'application/json'}
        OK=['webws.365scores.com','site.api.espn.com','www.fotmob.com','prod-cdn-public-api.livescore.com']
        async def route(r):
            u=r.request.url
            if u.startswith('file:'): return await r.continue_()
            if 'thor457' in u and 'markets.json' in u:
                return await r.fulfill(status=200,body=open('/home/claude/pronostici/state/markets.json').read(),headers=H)
            if 'thor457' in u and 'meta.json' in u:
                return await r.fulfill(status=200,body=open('/home/claude/pronostici/state/meta.json').read(),headers=H)
            if not any(h in u for h in OK): return await r.abort()
            pr=await asyncio.create_subprocess_exec('curl','-sS','--compressed','-m','45',u,stdout=asyncio.subprocess.PIPE); out,_=await pr.communicate()
            await r.fulfill(status=200,body=out,headers=H)
        await pg.route('**/*',route)
        await pg.goto(APP); await pg.wait_for_timeout(22000)
        r=await pg.evaluate("""async()=>{const o={fdm:!!window.FDM, n:window.FDM&&window.FDM.partite}; const E=window.PP, S=window.__S();
          o.t1=E.fdTeam('Inter Milan'); o.t2=E.fdTeam('Manchester City'); o.t3=E.fdTeam('Atalanta'); o.t4=E.fdTeam('Bayern Munich'); o.t5=E.fdTeam('Paris Saint-Germain');
          ['t1','t2','t3','t4','t5'].forEach(k=>o[k]=o[k]?o[k].name+' '+JSON.stringify(o[k].c):null);
          const ev={id:'x1',home:'Juventus',away:'Venezia',league:'ita.1',date:'2026-11-22T11:30:00Z'};
          o.ls=await window.__T.lsLineup(ev).then(x=>x?Object.keys(x).map(k=>k+':'+x[k].filter(p=>p.starter).length+'/'+x[k].length):null).catch(e=>'err '+e.message);
          o.out=(S.lsOut||{})['x1_0'];
          const S2=window.__S?window.__S():S; const lam={lh:1.6,la:0.9}; const m=E.statModel(S,{id:'y',home:'Como',away:'Torino',league:'ita.1'},lam,'corner'); o.sm=m&&[m.lh.toFixed(2),m.la.toFixed(2),m.n];
          return o}""")
        print(json.dumps(r,ensure_ascii=False,indent=1))
        await pg.click('nav button[data-t=altro]'); await pg.wait_for_timeout(1500)
        btn=await pg.query_selector_all('#app button, #app .card')
        txt=await pg.evaluate("()=>window.__T.mktHtml()")
        import re as _r; txt=_r.sub(r'<[^>]+>','',_r.sub(r'</(td|th)>',' | ',_r.sub(r'</tr>|</div>|</table>','\n',txt))); print(txt[:2600])
        print('errori:',errs)
        await b.close()
asyncio.run(main())
