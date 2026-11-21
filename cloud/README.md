# Addestramento 24 su 24

Ogni ora un'attività programmata esegue `python3 cloud/train.py 20`:
apre l'app senza schermo, carica `state/state.json`, lavora 20 minuti
(campionati principali, pronostici pre-partita, formazioni ufficiali, verifiche,
storico) e salva il nuovo `state/state.json` con `state/meta.json`.
Il telefono controlla `meta.json` ogni 10 minuti e, se c'è un modello più nuovo,
lo scarica e lo unisce al suo (le impostazioni, i tipster e i log restano quelli del telefono).
