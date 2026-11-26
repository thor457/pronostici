"""Audit delle consegne di Claude (data/consegne/AAAA-MM-GG.json) contro ESPN: ogni giocata nella versione e nell'ordine consegnati."""
import json,subprocess,sys,unicodedata,re
D=json.load(open(sys.argv[1]))
nm=lambda x:re.sub(r'[^a-z]','',unicodedata.normalize('NFKD',x).lower())
def same(a,b):
    a,b=nm(a),nm(b); return a==b or (len(a)>4 and len(b)>4 and (a[-6:]==b[-6:] or a in b or b in a))
def get(u): return json.loads(subprocess.run(['curl','-sS','-m','30',u],capture_output=True).stdout)
day=D['giorno'].replace('-','')
EV={}
for lg in set(v['lg'] for v in D['partite'].values()):
    for d in (day,):
        for e in get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard?dates={d}").get('events',[]):
            EV[e['id']]=(lg,[c['team']['displayName'] for c in e['competitions'][0]['competitors']])
def find(m,v):
    if v.get('eid'): return v['lg'],v['eid']
    h=m.split(' - ')[0]
    for i,(lg,n) in EV.items():
        if lg==v['lg'] and nm(n[0])[:5]==nm(h)[:5]: return lg,i
R={}; tot={}
def add(k,ok):
    t=tot.setdefault(k,[0,0]); t[0]+=1; t[1]+=bool(ok)
for m,v in D['partite'].items():
    lg,eid=find(m,v); s=get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/summary?event={eid}")
    comp=s['header']['competitions'][0]['competitors']; home=[c for c in comp if c['homeAway']=='home'][0]; away=[c for c in comp if c['homeAway']=='away'][0]
    gh,ga=int(home['score']),int(away['score'])
    ke=s.get('keyEvents',[])
    cards=[k['participants'][0]['athlete']['displayName'] for k in ke if 'Card' in k['type']['text'] and k.get('participants')]
    goals=[k['participants'][0]['athlete']['displayName'] for k in ke if 'Goal' in k['type']['text'] and 'Own' not in k['type']['text'] and k.get('participants')]
    subs=[(k['participants'][0]['athlete']['displayName'],k['participants'][1]['athlete']['displayName']) for k in ke if 'Sub' in k['type']['text'] and len(k.get('participants',[]))>1]
    ps={}
    for r in s.get('rosters',[]):
        for a in r.get('roster',[]):
            st={x['name']:x.get('value') for x in a.get('stats',[])}; ps[a['athlete']['displayName']]=st
    def pst(n,k):
        for kk,st in ps.items():
            if same(kk,n): return st.get(k) or 0
        return None
    ts={}
    for t in s.get('boxscore',{}).get('teams',[]):
        ts[t['homeAway']]={x['name']:float(x.get('displayValue') or 0) for x in t.get('statistics',[]) if str(x.get('displayValue','')).replace('.','').isdigit()}
    plus=lambda n:any(same(c,n) for c in cards) or any(same(c,i) for i,o in subs if same(o,n) for c in cards)
    out=[f"{m}: {gh}-{ga}"]
    if 'esatto' in v: ok=v['esatto']==f"{gh}-{ga}"; add('Risultato esatto',ok); out.append(f"  esatto {v['esatto']} {'✅' if ok else '❌'}")
    if 'direzione' in v:
        d=v['direzione']; ok={'1':gh>ga,'2':ga>gh,'X2':ga>=gh,'1X':gh>=ga,'Goal':gh>0 and ga>0}[d]; add('Direzione',ok); out.append(f"  direzione {d} {'✅' if ok else '❌'}")
    for n in v.get('marcatori',[]):
        ok=any(same(g,n) for g in goals); add('Marcatori',ok); out.append(f"  marcatore {n} {'✅' if ok else '❌'}")
    for n in v.get('tiri_in_porta',[]):
        x=pst(n,'shotsOnTarget'); ok=(x or 0)>=1; add('Tiri in porta del giocatore',ok); out.append(f"  tiro in porta {n}: {x} {'✅' if ok else '❌'}")
    for n in v.get('falli_fatti_1',[]):
        x=pst(n,'foulsCommitted'); ok=(x or 0)>=1; add('Falli fatti del giocatore',ok); out.append(f"  almeno 1 fallo {n}: {x} {'✅' if ok else '❌'}")
    for n in v.get('falli_subiti_1',[]):
        x=pst(n,'foulsSuffered'); ok=(x or 0)>=1; add('Falli subiti del giocatore',ok); out.append(f"  almeno 1 fallo subito {n}: {x} {'✅' if ok else '❌'}")
    mk=[]
    for i,n in enumerate(v.get('ammoniti',[])):
        ok=plus(n); add('Ammonito o sostituto',ok); own=any(same(c,n) for c in cards); mk.append(f"{i+1}. {n} {'✅' if own else ('✅ (sostituto)' if ok else '❌')}")
    if mk: out.append('  ammoniti consegnati: '+' · '.join(mk)+f" → presi {sum('✅' in x for x in mk)} su {len(mk)}")
    R[m]=dict(gh=gh,ga=ga,ts=ts,ps=ps,cards=cards,goals=goals,subs=subs)
    print('\n'.join(out))
# bomba
print('\nBOMBA (versione finale consegnata):'); ok_all=0
for m,k,a,line in D.get('bomba_finale',[]):
    r=R[m]; ts=r['ts']; gh,ga=r['gh'],r['ga']
    def T(side,key): return ts.get(side,{}).get(key,0)
    if k=='team_gol_over': val=gh if a=='home' else ga
    elif k=='team_sot_over': val=T(a,'shotsOnTarget')
    elif k=='team_corner_over': val=T(a,'wonCorners')
    elif k=='tot_falli_over': val=T('home','foulsCommitted')+T('away','foulsCommitted')
    elif k=='tot_sot_over': val=T('home','shotsOnTarget')+T('away','shotsOnTarget')
    elif k=='tot_corner_over': val=T('home','wonCorners')+T('away','wonCorners')
    elif k in('player_fs1','player_f1'):
        key='foulsSuffered' if k=='player_fs1' else 'foulsCommitted'; val=next((st.get(key) or 0 for kk,st in r['ps'].items() if same(kk,a)),None); line=0.5
    elif k=='team_segna': val=gh if a=='home' else ga; line=0.5
    elif k=='1X': val=1 if gh>=ga else 0; line=0.5
    elif k=='X2': val=1 if ga>=gh else 0; line=0.5
    ok=val is not None and val>line; ok_all+=ok; add('Bomba: gambe',ok)
    print(f"  {m} · {k} {a} {line}: {val} {'✅' if ok else '❌'}")
print(f"  gambe vinte {ok_all} su {len(D.get('bomba_finale',[]))}")
# LISTE E SCHEDINE CONSEGNATE NEL FORMATO DAL 26/11 (ammoniti_* con lista, schedine_* con gambe):
# ogni gamba con la probabilità detta prima del via, così l'app confronta detto e successo per categoria e si ricalibra
CAL={}; SEEN=set()
def cal(cat,p,ok):
    c=CAL.setdefault(cat,[0,0,0.0]); c[0]+=1; c[1]+=bool(ok); c[2]+=(p/100 if p>1 else p)
def sur(x): return nm(x.split()[-1])
def same2(a,b): return nm(a)==nm(b) or sur(a)==sur(b) or (len(sur(a))>4 and (sur(a) in nm(b) or sur(b) in nm(a)))
def fm(m):
    if m in R: return R[m]
    h,a=m.split(' - ',1)
    for k,r in R.items():
        kh,ka=k.split(' - ',1)
        if (nm(kh)[:5]==nm(h)[:5] or nm(kh)[:4] in nm(h)) and (nm(ka)[:3] in nm(a) or nm(a)[:3] in nm(ka)): return r
    for k,r in R.items():
        if nm(k.split(' - ')[0])[:5]==nm(h)[:5]: return r
def legcat(lab):
    if re.match(r'Corner ',lab): return 'Gamba: corner'
    if re.match(r'Tiri in porta ',lab): return 'Gamba: tiri in porta di squadra'
    if re.match(r'Falli totali',lab): return 'Gamba: falli totali'
    if re.match(r'Gol ',lab): return 'Gamba: gol (squadra o totali)'
    if lab in('1','X','2','1X','X2','12'): return 'Gamba: esito o doppia'
    if 'fallo subito' in lab or 'falli subiti' in lab: return 'Gamba: falli subiti del giocatore'
    if 'fallo commess' in lab or 'falli commessi' in lab: return 'Gamba: falli fatti del giocatore'
    if 'tiro in porta' in lab or 'tiri in porta' in lab: return 'Gamba: tiri in porta del giocatore'
    return 'Gamba: altro'
def gleg(g):
    r=fm(g['m']); lab=g['label']
    if not r: return None
    gh,ga=r['gh'],r['ga']; h=g['m'].split(' - ')[0]
    if lab in('1','X','2','1X','X2','12'): return ('1' if gh>ga else '2' if ga>gh else 'X') in lab
    mo=re.match(r'(Gol|Tiri in porta|Corner|Falli) (.+?) Over ([\d.]+)',lab)
    if mo:
        kind,who,th=mo.group(1),mo.group(2),float(mo.group(3)); key={'Tiri in porta':'shotsOnTarget','Corner':'wonCorners','Falli':'foulsCommitted'}.get(kind)
        T=lambda s:r['ts'].get(s,{}).get(key)
        if who=='totali': val=gh+ga if kind=='Gol' else (None if T('home') is None or T('away') is None else T('home')+T('away'))
        else:
            sd='home' if nm(who)[:5]==nm(h)[:5] else 'away'; val=(gh if sd=='home' else ga) if kind=='Gol' else T(sd)
        return None if val is None else val>th
    mo=re.match(r'(.+?) almeno (\d+) (fall\w+ commess\w+|fall\w+ subit\w+|tir\w+ in porta)',lab)
    if mo:
        n,k,typ=mo.group(1),int(mo.group(2)),mo.group(3); key='foulsCommitted' if 'commess' in typ else 'foulsSuffered' if 'subit' in typ else 'shotsOnTarget'
        for pn,st in r['ps'].items():
            if same2(pn,n):
                if not (st.get('appearances') or st.get('subIns')): return None  # non sceso in campo: non si conta
                return (st.get(key) or 0)>=k
    return None
for key,val in D.items():
    if key.startswith('ammoniti_') and 'preXI' not in key and isinstance(val,dict) and val.get('lista'):
        mk=[]
        for i,x in enumerate(val['lista']):
            r=fm(x['m'])
            if not r: continue
            own=any(same2(c,x['nome']) for c in r['cards']); viaS=any(same2(c,i2) for i2,o in r['subs'] if same2(o,x['nome']) for c in r['cards'])
            ok=own or viaS; add('Ammonito o sostituto',ok); cal('Ammonito o sostituto (nomi)',x.get('p',20),ok)
            mk.append(f"{i+1}. {x['nome']} {'✅' if own else ('✅ (sostituto)' if viaS else '❌')}")
        print(f"\n{key}: "+' · '.join(mk)+f" → presi {sum('✅' in z for z in mk)} su {len(mk)}")
    if key.startswith('schedine_') and isinstance(val,list):
        for s in val:
            if not isinstance(s,dict) or not s.get('gambe'): continue
            rr=[(g,gleg(g)) for g in s['gambe']]; known=[z for z in rr if z[1] is not None]
            for g,ok in known:
                if (g['m'],g['label']) in SEEN: continue  # stessa gamba in più schedine: conta una volta
                SEEN.add((g['m'],g['label'])); cal(legcat(g['label']),g.get('p',80),ok)
            whole=all(ok for g,ok in known) and len(known)==len(rr)
            add('Schedine intere',whole)
            print(f"\n{key} · {s.get('nome')}: gambe vinte {sum(ok for g,ok in known)} su {len(known)}"+(f" ({len(rr)-len(known)} non verificabili)" if len(known)<len(rr) else '')+(' → VINTA' if whole else ' → PERSA'))
            for g,ok in known:
                if not ok: print(f"   ❌ {g['m']} · {g['label']} (detto {g.get('p')}%)")
print('\nDETTO PRIMA DEL VIA CONTRO SUCCESSO, PER CATEGORIA:')
for k,(n,h,sp) in sorted(CAL.items()): print(f"  {k}: {h} su {n} ({h/n*100:.0f}%), detto {sp/n*100:.0f}%")
print('\nTOTALI PER TIPO:')
for k,(n,h) in tot.items(): print(f"  {k}: {h} su {n} ({h/n*100:.0f}%)")
json.dump(dict(tot=tot,cal=CAL),open(sys.argv[1].replace('.json','_esito.json'),'w'),ensure_ascii=False)
