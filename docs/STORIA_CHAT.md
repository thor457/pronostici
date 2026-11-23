# Pronostici Pro — filo continuo della chat

Questo file serve a non perdere nulla quando la chat viene compressa. Va letto **prima di ogni lavoro sull'app** e aggiornato **alla fine di ogni richiesta** (nuove richieste dell'utente parola per parola, cosa è stato fatto, cosa resta).

Il testo integrale della chat resta comunque conservato da Claude: si recupera con gli strumenti `conversation_search` e `read_conversation` (conversation_id `current`, oppure cercando le parole chiave). Questo file è l'indice ragionato; la chat è la fonte parola per parola.

## Come si lavora sull'app

- Repository: `thor457/pronostici` (pubblico). L'app scarica da sola `index.html` da `https://raw.githubusercontent.com/thor457/pronostici/main/index.html`: niente APK a ogni versione.
- **Modificare sempre l'`index.html` del repository** (è la versione viva). Più sessioni Claude ci lavorano: prima `git pull --rebase`, poi modifiche, poi push. Non ricostruire da sorgenti vecchie (si cancellerebbero le modifiche delle altre sessioni).
- Commit con le righe finali:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` e `Claude-Session: https://claude.ai/code/session_01WpVRwcu9872r72ryJU6a4o`
- Addestramento 24 su 24: attività programmata «Pronostici Pro: addestramento orario nel cloud» (ogni ora al minuto 36), esegue `python3 cloud/train.py 20` e pubblica `state/state.json` e `state/meta.json`. Il telefono controlla `meta.json` ogni 10 minuti e unisce il modello (restano del telefono: impostazioni, log, video, Telegram).
- Prove: Playwright con le chiamate passate da `curl` (ESPN, 365Scores, FotMob, OLBG raggiungibili dal server).

## Fonti: cosa raggiunge chi (verificato il 23/11/2026)

| Fonte | Cloud (server) | Telefono |
|---|---|---|
| ESPN, 365Scores, FotMob | sì | sì |
| OLBG | sì (20 consigli per giro) | no risposta (lo riceve dal cloud) |
| WinDrawWin | anti-bot | sì |
| Forebet, Predictz | anti-bot | da verificare (vie alternative r.jina.ai e proxy) |
| SofaScore | rifiuto 403 | da verificare (vie alternative) |
| YouTube sottotitoli (Tipzone_TV) | «conferma di non essere un bot» | sì, quando ci sono i sottotitoli (dopo la fine della diretta) |
| MondoPengwin | sì dal 23/11 con browser vero (Chromium col proxy, `REAL` in train.py); passa al telefono come `ytw` | da verificare |
| Telegram canale privato t.me/c/… | no | solo inoltrando i messaggi a un bot dell'utente (codice in Altro → Tipster) |
| football-data.co.uk (statistiche ufficiali partita per partita + quote apertura/chiusura, 22 campionati) | sì | lo riceve dal cloud (state/markets.json) |
| LiveScore (formazioni, indisponibili, incidenti, statistiche con xG) | sì | sì (CORS aperto) |
| Understat, Transfermarkt, OddsPortal, BetExplorer, Flashscore (pagina) | raggiungibili, non ancora usati | — |
| FBref, WhoScored, footystats, bet365 | anti-bot | — |

## Richieste dell'utente in questa chat (parole sue, in ordine)

Dal riassunto della prima parte della chat (testo riportato fedelmente):
1. «Tutte le partite devono avere analisi e tutti i tipi di pronostici per gli addestramenti, aggiornamenti di ragionamento, analisi, pronostici eccetera.»
2. «https://www.sofascore.com/it Integra nell app come riferimento per i live in diretta di ogni partita e sopratutto questa schermata deve essere come sul sito poi dati e tutte le informazioni disponibili dettagliate come aul sito aggiornamenti ecc!!! Sfrutta tutti i dati che ci occorrono da softascore»
3. «L'app non funziona nel modo giusto. Primo, sono poche le partite addestrate. Il palinsesto è minimo… tasto indietro… Premendo due volte esco… più fonti ufficiali… multipla … date … quante partite … opzioni … tasto cerca … arbitri … quadro partite … tensione, posta in palio … risultati esatti con percentuale più alta…»
4. «L'app è diventata molto lenta, dobbiamo ottimizzarla tutta e in più il tasto circa deve comparire nel quadro primario.»
5. «Questo non deve accadere, dobbiamo avere sempre tutto disponibile. Quindi introduci SoftScore al 100% o altri siti simili con dati affidabili al 100% per avere sempre informazioni vere e dettagliate.»
6. «Nella schermata live questa deve esattamente comparire come soft score, quindi con tutti i dettagli… palla in movimento con la selezione dei giocatori, chi ha la palla, movimento fluido… Prendi direttamente quella e mettila qui.»
7. «L'app è ancora troppo lenta, prima cosa. Seconda cosa, ci sono degli errori nell'addestramento, non ci devono essere… Poi cerchiamo un modo per aggiornare direttamente l'app, senza che ogni volta dobbiamo scaricare l'APK.»
8. «Ora guidami per l'aggiornamento diretto che farai stesso tu, e da lì controllerai anche che l'addestramento sta procedendo bene…»
9. «Crea l'accesso diretto con GitHub, così farai tu tutto.»
10. «Controlla stesso tu che funzioni tutto correttamente, e il quadro principale impiega molto tempo a caricarsi e scorrere da una pagina all'altra.»
11. «Dobbiamo rendere tutto automatico da qua, quindi l'app la devi aggiornare direttamente senza fare ogni volta inserire il sito eccetera.»
12. «Ora fai un rapporto completo, di tutto… Dobbiamo introdurre qualche altra cosa per intensificare e aumentare la precisione millimetrica di ogni singolo pronostico.»
13. «Completa tutto, devi funzionare tutto al 100%.»
14. «Nella sezione Precisione, tutto deve essere scritto in italiano e in modo comprensibile, tipo BTTS o cose del genere, tutto italiano e comprensibile.»
15. «Tutti devo addestrare o perfezionare la precisione e metodo»
16. «Quando premo su qualsiasi partita iniziata deve partire automaticamente il live con tutti i dati e partita visibile»
17. «La palla deve muoversi live con tuttigli eventi e il giocatore xhe qualsiasi azioni 2 i cartellini e marcatori dopo un attenta analisi devono essere ragionati e scelti i migliori!!! Alle 23:30 ci dono partite del calcio brasiliano con tantissimi cartellini e marcatori e lapp non mi ha segnalato nulla in piu dice dati insufficiente NON DEVE ACCADERE»

Dalla seconda parte (testo integrale):
18. (19/11 23:24) «SU TUTTE LE PARTITE!!»
19. (20/11 05:53, screenshot Tipster) «Tipster Kata. Qui devono comparire tutte le percentuali dei migliori tipster su un determinato pronostico di tutte le partite possibili, e anche nelle multiple ci deve essere una sezione tipster dove i tipster combaciano sulla stessa, sullo stesso pronostico di una determinata partita.»
20. (20/11 13:00) «Aggiungi altri tipster professionisti di tutto il mondo. In più ci deve essere comunque un ragionamento su tutti i tipi di pronostici. Quindi i tipster forniscono un'indicazione, ma il ragionamento profondo lo deve fare l'app con dati storici, dati reali aggiornati in tempo reale dell'ultimo minuto, dell'ultima ora, eccetera, eccetera.»
21. (20/11 13:11) «Deve entrare in gioco anche soft score, è fondamentale.»
22. (20/11 16:32) «Dobbiamo incrementare fonti e metodo. Gli addestramenti devono produrre molto di più, andiamo molto a rilento. C'è bisogno di un prompt ancora più intenso e selettivo per tutti i tipi di pronostici. Per la serie A di domani voglio che l'app sia funzionante al 100% e con precisione e ragionamento molto intensi e affidabili su base di addestramento e ragionamento.»
23. (20/11 16:44) «Nel quadro devo vedere le partite dei campionati maggiori di tutta la giornata, con preanalisi già fatta, tensione, cartellini, marcatori forti, eccetera. Nei campionati maggiori, soprattutto la Serie A, deve essere sempre disponibile, non solo i live. Nel quadro, i live sono inutili, li posso guardare nella sezione live. Nel quadro devo vedere tutto quello che si può ancora giocare.»
24. (20/11 17:09) «https://www.youtube.com/live/Z6uCJVK0MRA?si=ZLKA42dIjxypDcIa Questo è un raduno di tipster che ragiona sulla serie A. Voglio che venga sempre preso in considerazione ogni settimana, ogni volta che fanno un live, eccetera. Tutto il live deve essere analizzato minuto per minuto e poi verrà effettuato il nostro ragionamento sul loro discorso. Non deve essere un'imposizione, ma noi dobbiamo effettuare un ulteriore aggiornamento. L'app deve effettuare un ulteriore aggiornamento e teniamo conto delle scelte dei migliori tipster.»
25. (20/11 17:10) «https://youtu.be/gWxDwQOIAvw»
26. (20/11 17:12) «https://t.me/c/1004557063/17907»
27. (20/11 17:24) «I link sono quelli, quindi completa tutto, deve essere tutto accessibile ogni volta che pubblicano qualcosa.»
28. (20/11 17:26) «https://www.mondopengwin.it/studio-top-campionati/»
29. (20/11 17:32) «Dai video dei tipster l'app deve ricavare tutto un ragionamento e i dati che forniscono, poi lei deve elaborare insieme ai dati dei tipster storico, dati attuali eccetera eccetera eccetera per definire ogni singolo pronostico. Ti ho inserito tutti i dati, tra cui i video di YouTube di Tip Zone che pubblicano ogni settimana, ogni tanto, che ci sono più tipster professionisti. Quindi quelli ci servono per incrociare i nostri dati e anche il mondo penguin.»
30. (20/11 17:34, screenshot) live Tipzone «Serie A – Giornata 12», 20 novembre ore 18:00.
31. (20/11 22:38, screenshot Live) «Nella sezione live quando clicco sopra devo vedere la partita con tutte le informazioni come softa score!!»
32. (21/11 10:46, screenshot Multipla) «Qui devo anche poter selezionare il campionato dove intendo creare la multipla e quando metto ad esempio quota 50, oltre alle basi solide ci deve essere anche il ragionamento per i pronostici ad alta quota, ma con base di ragionamento solido, in base ai dati, le informazioni attuali, le ultime interviste, eccetera.»
33. (21/11 11:01, screenshot Tipster con OLBG/Forebet/SofaScore «signal is aborted»)
34. (21/11 11:21, screenshot esatti) «I tisultati esatti devono essere il piu accurati possibile!! Quindi lapp deve eseguire un ragionamento molto complesso analizzare ogni dettaglio forma assenza direzione ecccc tutti i dati e informazioni devono essere incrociati e elaborati in modo impeccabile»
35. (21/11 11:26, screenshot Quadro) «Vedo che l'app trova poche ufficiali. Deve elaborare tutte le partite quotidiane per perfezionare metodo, ragionamento e precisione per tutti i tipi di pronostici. Le ufficiali servono anche per i marcatori e soprattutto i giocatori ammoniti o loro sostituti. Quindi la ricerca deve avvenire in modo continuo ed effettivo prima del calcio d'inizio, in modo da dare tutti i tipi di pronostici e addestrare l'app per aumentare la perfezione ogni ora di più.»
36. (21/11 11:30-11:31) «In più, da questa giornata di Serie A voglio un addestramento intensivo e correzione di ragionamenti in base agli errori, apprendimento di ragionamento, apprendimento di pronostici, tutto, qualsiasi cosa per rendere l'app sempre più vicina alla percentuale di precisione del 90% in tutti i tipi di pronostici, ragionamenti, ricerca informazioni, eccetera, eccetera, eccetera, come un vero professionista. Oltre alla Serie A ci sono anche tantissime partite dei campionati importanti. Stessa cosa deve avvenire per quelli.»
37. (21/11 11:37) «Questo deve avvenire in modo continuo 24su24»
38. (23/11 09:35) «Prova adesso a inserire tutto.»
39. (23/11 09:37) «Allora, dobbiamo raggiungere tutti i siti. Ho abilitato i domini, quindi inserisci anche tutti i tipster che avevamo detto prima, le pagine dei tipster, e in più tutti i limiti che hai messo devono essere tutti abilitati.»
40. (23/11 09:52) «Tutta questa chat va conservata, nel senso che non devi perdere alcuna parola detta quando comprimi la chat, quindi fai in modo tale che tu riesca a ricordare ogni singola parola detta dall'inizio di questa chat, sempre, in modo tale da avere un filo continuo. Trovo un metodo, la soluzione, ma deve essere sempre estesa al 100% per non perdere i dettagli della conversazione.»

41. (23/11 09:56) «Ok, testa ogni cosa dell'app, deve essere funzionante al 100%, in più deve addestrare anche il ragionamento, oltre a tutti i fattori già detti.»

42. (23/11 11:41, screenshot Addestramento) «In questa sezione vanno caricati tutti i campionati 2025-2026, inclusi quelli che verranno, per avere un quadro ancora più completo, con audit, pre-pronostici e poi confronto finale, in modo tale di addestrare tutti i metodi, ragionamento e precisione.»

43. (23/11 11:46) «Epsilon e footmob. Dobbiamo aggiungere altre fonti molto dettagliate, altri siti, tipo SoftScore, tutti i siti che hanno dettagli esatti e ufficiali, in modo tale da essere precisi al 100% e acquisire ancora più dati. L'addestramento deve essere completo su tutti i tipi di pronostici che offrono i bookmakers, eccetera, eccetera.»

44. (23/11 12:16) «Ok, quello che restano bloccati dobbiamo inserirli. Troviamo la soluzione.»

45. (23/11 12:50, screenshot Fonti dal telefono: ESPN 403, 365Scores/FotMob/SofaScore live/LiveScore/GitHub OK, SofaScore palinsesto 403, FBref anti-bot, FootyStats/Forebet/WhoScored/Transfermarkt/MondoPengwin OK, Understat pagina senza dati) «Risolvi tutto.»

46. (23/11 13:19, screenshot Fonti: SofaScore palinsesto 403, FBref anti-bot, Understat senza dati, il resto OK) senza testo.

47. (23/11 14:24, screenshot Fonti con molte righe «non ancora provata») «Dobbiamo risolvere a uno tutti questi problemi. Deve essere tutto completamente e perfettamente funzionante.»

48. (23/11 14:31) «Ti ripeto che tutto deve funzionare esattamente. Se c'è bisogno per la prima volta di una verifica umana, eccetera, dammi il link, lo faccio io, poi devi proseguire tutto automaticamente e completamente.»

49. (23/11 14:37, screenshot Quadro con solo Monza-Fiorentina, Brentford-Everton, Levante-Elche oggi) «Tutte le partite importanti di oggi si sono ridotte a queste tre? No, non sta funzionando assolutamente per niente bene. Devi ottimizzare tutto. Ricerca cose che già abbiamo detto in tutta la chat.»

50. (23/11 14:56) «L'addestramento deve procedere con tutto il palinsesto quotidiano, ogni giorno. Addestramento di ragionamento, addestramento di precisione, addestramento di correzione, eccetera, eccetera, eccetera. Quindi per ogni partita ci sarà sempre un prepronostico alle ufficiali e non, e poi audit completo. Per perfezionamento e correzione del metodo in sé, quindi ragionamento, analisi, ricerca dati e tutti i tipi di pronostici, risultati esatti, i cartellini, arbitri, eccetera, eccetera, eccetera, come abbiamo già detto.»

51. (23/11 15:55) «Verfica che tutto funzioni alla perfezione»

## Cosa è stato fatto (sintesi per richiesta)

- 17-18: dati FotMob su tutte le partite (ultime 5 di ogni squadra, rose, falli, cartellini, xG), ammoniti e marcatori ricalcolati; Brasile coperto.
- 19-21: tipster automatici (OLBG, Forebet, WinDrawWin, voti 365Scores e SofaScore, quote con movimento), sezione «Fonti che combaciano», «Tipster concordi» e «Multipla dei tipster concordi»; sezione Ragionamento in ogni partita (ultima ora, dati, esito, gol, Goal/No Goal, esatto, cartellini, marcatori, sintesi).
- 22: Selezione Pro (filtri severi), campionati principali completi da FotMob, classifica e posta in palio, addestramento 6 schede in parallelo e storico fino a 14 mesi.
- 23: Quadro solo partite giocabili, campionati maggiori fino a dopodomani con preanalisi; corretti i nomi delle squadre nell'archivio di forza (Manchester City ecc.), stima da classifica per le squadre sconosciute.
- 24-30: tipster in video (sottotitoli YouTube minuto per minuto, scelte e dati citati, verifica assenze con FotMob), pagine web (MondoPengwin), Telegram via bot; pronostico finale che fonde dati e tipster pesati per affidabilità.
- 31: Live che si apre subito anche con SofaScore lento; minuto stimato al posto di «Started».
- 32: Multipla con scelta del campionato e «Alta quota ragionata» con dati, fonti e scenario di perdita.
- 33: vie alternative per i siti bloccati (r.jina.ai, proxy), errori in italiano.
- 34: esatti con distribuzione reale dei gol, pareggi del campionato, esatti dei tipster, sempre dentro la direzione, spiegazione «Come è stato scelto».
- 35: formazioni ufficiali in continuo (365Scores, FotMob, ESPN), ammoniti e marcatori ricalcolati sull'XI e registrati per l'addestramento.
- 36: apprendimento dagli errori (attacco/difesa di ogni squadra), pagina «Errori e correzioni».
- 37-38: addestramento orario nel cloud attivo (vedi sopra).
- 39: OLBG letto dal cloud e passato al telefono; voti e quote 365Scores su tutte le partite delle prossime 48 ore; gli altri siti respingono i server (tabella fonti).
- 40: questo file + riga nella memoria che obbliga a leggerlo.
- 41: collaudo completo automatico `cloud/test_app.py` (22 controlli: avvio, tutte le schede, tre multiple, tutte le pagine di Altro, tutte le sezioni di una partita, centro live con tutte le schede, tasto indietro): 22 su 22. Addestramento del ragionamento: registro `S.rag` dei fattori (dati dell'app, bookmaker, accordo/disaccordo e chi aveva ragione, quote in calo, tipster concordi, video, tensione e gialli, ammoniti con/senza XI, gol attesi alti/bassi) aggiornato a ogni verifica; il pronostico finale si sposta verso il mercato o verso i dati secondo chi ha avuto più ragione nei disaccordi (da 15 casi); sezione «Ragionamento appreso» nella partita e in Errori e correzioni. Lavoro in sottofondo in pausa mentre si apre una partita dal vivo.
- 42: ripasso delle stagioni 2025-26 e 2026-27 (`replayStep`, stato `S.rp`): modello ombra dal 1/7/2025, giorno per giorno, tutti i campionati ESPN (maggiori a parte), pre-pronostico con i soli dati di prima (anche quote pre-partita ESPN), confronto e poi apprendimento; statistiche per stagione, campionati maggiori e mese per mese nella pagina Addestramento; gira nel ciclo dell'app (4 giorni ogni 2 minuti) e nel cloud (fino a un terzo di ogni giro). Prova: 20 giorni di luglio 2025, 851 partite.
- 43: `cloud/markets.py` (gira all'inizio di ogni addestramento orario): statistiche ufficiali football-data.co.uk di 22 campionati, 2025-26 e 2026-27 (10.096 partite al 23/11): per ogni gara, con i soli dati di prima, pronostico e verifica di 161 mercati (gol totali e di squadra 0,5-4,5, 1° e 2° tempo, tempo con più gol, 1X2 solo dati / dati+quote / solo quote, doppia chance, Goal/No Goal, esatto e uno dei 3, handicap asiatico, corner/gialli/tiri/tiri in porta/falli totali e di squadra su più linee, chi ne fa di più e doppia chance della statistica, rosso sì/no), taratura imparata in corsa, arbitro per i gialli. Esce `state/markets.json` (medie squadra casa/fuori, arbitri, tabelle di taratura, risultati per mercato e campionato); `meta.json` porta `mk`. L'app lo scarica (`window.FDM`, IndexedDB `fdm`), usa le medie ufficiali in `E.statModel` quando mancano quelle ESPN e i gialli di squadra per i mercati cartellini; nuova sezione «Tutti i mercati dei bookmaker» in Addestramento con scelta del campionato. LiveScore aggiunto come quarta fonte delle formazioni ufficiali (entro 80' dal via) con elenco indisponibili (`S.lsOut`). Risultato onesto: sull'1X2 le quote battono il modello solo dati, per questo si uniscono.
- 44: prove dal cloud (23/11): SofaScore 403 anche dai proxy pubblici; FBref, FootyStats, Forebet con verifica Cloudflare interattiva anche con browser vero; WhoScored blocco Cloudflare; MondoPengwin risponde a un browser vero → aggiunto al cloud (fase 2c) e passato al telefono. Non si aggirano CAPTCHA o verifiche anti-bot. Telefono: SofaScore era interrotto a 6 s (palinsesto di alcuni MB) → 25 s; in Altro → Fonti la prova diretta di SofaScore, FBref, FootyStats, Forebet, WhoScored, Understat, Transfermarkt, MondoPengwin, con esito anche nel «Rapporto per Claude», per collegare i lettori dei siti che dal telefono rispondono.
- 45: ESPN 403 dal telefono = troppe richieste dallo stesso telefono → pausa automatica di 10 minuti (`E.espnOff`) e il telefono salta lo storico pesante (campionati, ripasso stagioni, storico, archivio arbitri) quando ha un modello del cloud di meno di 4 ore (`cloudFresh`). SofaScore: se il palinsesto risponde 403 la partita si cerca fra quelle in corso e poi per squadra (`search/teams`, `team/{id}/events/next|last`). Transfermarkt: infortunati di 13 campionati con ruolo, infortunio e rientro (`P.tmInjuries`, `S.tmInj`, anche dal cloud, unione per data). FootyStats e WhoScored: lettura delle tabelle della pagina dal telefono ogni 12 ore (`siteStep`, `S.wt`, solo telefono), righe della squadra nella scheda «Formazioni, assenti, arbitro» con gli indisponibili LiveScore (`siteHtml`). Forebet e MondoPengwin erano già letti. FBref (anti-bot anche dal telefono) e Understat (pagina di errore per tutti): sostituiti da FotMob (statistiche Opta), football-data e LiveScore (xG).
- 46: in Fonti nuova prova «SofaScore ricerca partita» (quella che conta: id trovato anche senza palinsesto); FBref e Understat marcati come NON USATI con la fonte che li sostituisce.
- 47: causa: le prove in Fonti erano in fila e la ricerca SofaScore passava per 4 proxy pubblici con 25 s ciascuno, bloccando le prove successive. Ora: tutte in parallelo con massimo 35 s ciascuna (`cloud/test_fonti.py`: tutte concluse entro 40 s); SofaScore solo via diretta (niente proxy pubblici); id delle squadre SofaScore imparati da ogni elenco live e salvati (`pp_sofat`), ricerca con `search/all` e `search/teams`, poi `team/{id}/events/next|last` per casa e ospite.
- 48: Understat risponde a tutti «We will come back soon» (manutenzione, non una verifica): lettore `P.usParse` (teamsData, xG/xGA/npxG/PPDA ultime 8 gare) che riprova ogni 6 ore e si attiva da solo quando il sito torna; dati nella scheda partita. FBref: spiegato all'utente che una verifica fatta una volta non può reggere la lettura automatica (permesso legato a telefono e rete, scade, e il cloud non può usarlo) e che non costruisco un modo per far passare letture automatiche oltre una verifica anti-bot; dati Opta da FotMob. SofaScore palinsesto: rifiuto dell'API, non una verifica; coperto dalla ricerca partita.
- 49: verificato su FotMob/ESPN: lunedì 23/11 i 5 campionati maggiori avevano davvero solo quelle 3 partite; ma il Quadro escludeva le altre importanti. Ora `IMPLG` (Quadro e priorità di analisi): 5 maggiori, coppe europee e mondiali, Serie B e seconde divisioni di Inghilterra/Spagna/Germania/Francia, Portogallo, Olanda, Turchia, Belgio, Scozia, Grecia, Austria, Svizzera, Danimarca, coppe nazionali, AFC Champions, Libertadores/Sudamericana, Brasile, Argentina, MLS, Messico, Arabia; ordine Serie A → big 4 + Champions → altre UEFA/Serie B/Coppa Italia → seconde e medie leghe → resto. Le partite ESPN del flusso «tutti i campionati» prendono il codice di lega da 365Scores (`E.C365`, id competizione → codice ESPN); doppioni con nomi diversi (Inter/Internazionale, Slavia Praha/Prague, PSG) fusi (`near2`). Analisi in sottofondo con 5 lavori insieme invece di 3. Prova (`cloud/test_quadro.py`): oggi 16 partite importanti, domani 26, nessun doppione.
- 50: prima la copertura era parziale (es. 22/11: 514 partite, 3 pre-pronostici). Ora `palinsestoStep(giorni, msProfondi)`: pre-pronostico leggero (calcolo locale) di TUTTE le partite di oggi e domani + registrazione di tutti i mercati (`S.picks` in `prepEv`), poi analisi profonda (probabili, assenti, arbitro, ultime partite) per importanti e vicine finché c'è tempo; telefono ogni 30 min (solo leggero), cloud a ogni giro (30% del tempo). Cloud: `pollLU` in continuo per tutto il giro (ufficiali escono ~60' prima, un giro di 20' ogni ora le prende tutte); verifica e audit di tutte le finite di ieri l'altro, ieri e oggi con 4 lavori. Verifica separata del pre-pronostico prima delle ufficiali (`S.ver[id].pre`) per misurare l'effetto delle ufficiali per tipo. Copertura per giorno `S.cov` (partite, pre-pronostico, con XI, verificate) e scheda «Palinsesto quotidiano completo» in Addestramento. Errori trovati e corretti: partite 365Scores rinviate o «solo risultato finale» trattate come finite 0-0 (ora stato `off`, escluse); cartellini «0» quando la cronaca era incompleta (ora contano solo se tutti i gol del risultato sono nella cronaca); cartellini totali verificati come Over sotto la media attesa invece della fascia MEDIA (= esattamente 4). Tolte dal registro 18 verifiche false 0-0. Prova nel cloud: 273 partite da giocare con pre-pronostico (155 nuove), 228 analisi profonde, 25 XI ufficiali in un giro di 10'.
- 51: verifica completa. Passano: collaudo 22/22, Fonti (tutte le prove chiuse entro 40 s), Quadro (16 partite oggi, 26 domani, nessun doppione), Transfermarkt (13 campionati), verifica simulata prima/dopo le ufficiali su 4 partite di Serie A e Liga. Errori trovati e corretti: (1) lo storico ricostruiva un pronostico per ogni vecchia partita imparata, riempiva l'archivio (2500) e CANCELLAVA i pre-pronostici delle partite di domani (nel giro orario ne restavano 75 su 285): ora ricostruzione solo per partite degli ultimi 3 giorni e l'archivio non toglie mai le partite da giocare (prima le verificate, poi le ricostruite); controllo con conteggio dopo ogni fase in `train.py` (285 stabili fino alla fine). (2) Transfermarkt a volte rispondeva con pagina ridotta a richieste ravvicinate: un secondo tentativo dopo 6 s e 1,5 s fra i campionati. (3) giocatori dell'archivio di partenza con lettere speciali (ø…) avevano chiavi non normalizzate (dati non trovati, nome illeggibile «leoøstigard»): unite alla chiave giusta a ogni avvio. (4) vecchie verifiche dei cartellini a fascia riconvertite in Over sotto la media attesa.

## Limiti dichiarati all'utente (da non nascondere)

- Il 90% è realistico solo sulle giocate più sicure; esito secco, esatti, ammoniti e marcatori restano molto più bassi (lo mostra la pagina Precisione).
- Posizione della palla secondo per secondo: nessuna fonte gratuita; il campo live si muove evento per evento.
- Campionati dilettanti: spesso solo punteggio e statistiche base.
