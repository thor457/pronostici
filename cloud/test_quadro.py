import asyncio, re
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':390,'height':844})
        H={'access-control-allow-origin':'*','content-type':'application/json'}
        OK=['webws.365scores.com','site.api.espn.com','www.fotmob.com']
        async def route(r):
            u=r.request.url
            if u.startswith('file:'): return await r.continue_()
            if not any(h in u for h in OK): return await r.abort()
            pr=await asyncio.create_subprocess_exec('curl','-sS','--compressed','-m','45',u,stdout=asyncio.subprocess.PIPE); out,_=await pr.communicate()
            await r.fulfill(status=200,body=out,headers=H)
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/pronostici/index.html'); await pg.wait_for_timeout(60000)
        t=await pg.inner_text('#app'); i=t.lower().find('campionati maggiori e importanti'); seg=t[i:i+30000]; print(i, len(t))
        for line in seg.split('\n'):
            if re.match(r'^\d\d:\d\d · ',line) or line.upper() in ('OGGI','DOMANI') or 'NOVEMBRE' in line.upper(): print(line[:80])
        await b.close()
asyncio.run(main())
