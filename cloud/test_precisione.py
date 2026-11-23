import asyncio, json, re
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        H={'access-control-allow-origin':'*','content-type':'application/json'}
        OK=['webws.365scores.com','site.api.espn.com','www.fotmob.com']
        async def route(r):
            u=r.request.url
            if u.startswith('file:'): return await r.continue_()
            if not any(h in u for h in OK): return await r.abort()
            pr=await asyncio.create_subprocess_exec('curl','-sS','-L','--compressed','-m','45',u,stdout=asyncio.subprocess.PIPE); out,_=await pr.communicate()
            await r.fulfill(status=200,body=out,headers=H)
        await pg.route('**/*',route)
        prev=open('/home/claude/pronostici/state/state.json').read()
        await pg.add_init_script('window.__CLOUD=true; window.__PRELOAD_S=' + prev + ';')
        await pg.goto('file:///home/claude/pronostici/index.html'); await pg.wait_for_timeout(6000)
        r=await pg.evaluate("""async()=>{const T=window.__T; let L=[]; for(const k of [0,1]) L=L.concat(await T.dayEvents(new Date(Date.now()+k*864e5)));
          const strip=h=>h.replace(/<\\/tr>|<br>|<\\/div>/g,'\\n').replace(/<\\/t[dh]>/g,' | ').replace(/<[^>]+>/g,'').replace(/\\n\\s*\\n/g,'\\n');
          return {real:strip(T.realHtml()), hp:strip(T.hpHtml(L,15))}}""")
        print(r['real'][:4500]); print('=================='); print(r['hp'][:4000]); print(errs[:3]); await b.close()
asyncio.run(main())
