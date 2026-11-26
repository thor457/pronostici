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
print('\nTOTALI PER TIPO:')
for k,(n,h) in tot.items(): print(f"  {k}: {h} su {n} ({h/n*100:.0f}%)")
json.dump(dict(tot=tot),open(sys.argv[1].replace('.json','_esito.json'),'w'),ensure_ascii=False)
