import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':390,'height':844})
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        H={'access-control-allow-origin':'*','content-type':'text/html'}
        OK=['www.transfermarkt.it','prod-cdn-public-api.livescore.com','webws.365scores.com','www.fotmob.com','site.api.espn.com','raw.githubusercontent.com','api.sofascore.com']
        async def route(r):
            u=r.request.url
            if u.startswith('file:'): return await r.continue_()
            if not any(h in u for h in OK): return await r.abort()
            pr=await asyncio.create_subprocess_exec('curl','-sS','--compressed','-m','45','-A','Mozilla/5.0',u,stdout=asyncio.subprocess.PIPE); out,_=await pr.communicate()
            await r.fulfill(status=403 if 'sofascore' in u else 200,body=out,headers=H)
        await pg.route('**/*',route)
        await pg.goto('file:///home/claude/pronostici/index.html'); await pg.wait_for_timeout(5000)
        await pg.click('nav button[data-t=altro]'); await pg.wait_for_timeout(1000)
        await pg.evaluate("()=>{const b=[...document.querySelectorAll('#app *')].find(x=>/^Fonti/.test(x.innerText||'')&&x.onclick);}")
        t=await pg.evaluate("()=>{const el=[...document.querySelectorAll('[data-k=fonti],[data-v=fonti]')]; return el.length}")
        await pg.click('text=Prova quali siti risponde')
        for sec in (5,20,40):
            await pg.wait_for_timeout(sec*1000 if sec==5 else 15000)
            txt=await pg.inner_text('#app'); print('---',sec, txt.count('non ancora provata'), txt.count('prova in corso'), txt.count('OK ·'), txt.count('non raggiungibile'))
        print(txt[:2500]); print(errs); await b.close()
asyncio.run(main())
