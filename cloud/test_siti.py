import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        H={'access-control-allow-origin':'*','content-type':'text/html'}
        OK=['www.transfermarkt.it','prod-cdn-public-api.livescore.com']
        async def route(r):
            u=r.request.url
            if u.startswith('file:'): return await r.continue_()
            if not any(h in u for h in OK): return await r.abort()
            pr=await asyncio.create_subprocess_exec('curl','-sS','--compressed','-m','45','-A','Mozilla/5.0',u,stdout=asyncio.subprocess.PIPE); out,_=await pr.communicate()
            await r.fulfill(status=200,body=out,headers=H)
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/pronostici/index.html'); await pg.wait_for_timeout(4000)
        r=await pg.evaluate("""async()=>{const T=window.__T,S=window.__S(); const n=await T.siteStep(); const I=S.tmInj;
          const o={n, lg:Object.keys(I).map(k=>k+' '+((I[k].L||[]).length)+(I[k].err?' '+I[k].err:'')), es:(I['ita.1'].L||[]).slice(0,3), wt:Object.keys(S.wt).map(k=>k+' '+S.wt[k].err)};
          o.html=T.siteHtml({id:'z',league:'ita.1',home:'Juventus',away:'Cagliari'}).replace(/<[^>]+>/g,' ').slice(0,700); return o}""")
        print(json.dumps(r,ensure_ascii=False,indent=1)); print(errs); await b.close()
asyncio.run(main())
