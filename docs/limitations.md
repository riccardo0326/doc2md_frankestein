# Limiti Attuali Del Software

**Data:** 2026-10-28  
**Stato:** relazione tecnica sullo stato della migrazione, non piano di
implementazione.

## Sintesi

Il software gestisce bene il percorso locale AnyDoc per pagine PDF digitali
prevalentemente testuali. Il limite più importante riguarda le immagini
embedded presenti dentro pagine classificate `TEXT`.

Una pagina può contenere testo estraibile e, contemporaneamente, una figura,
essenziale. Oggi quella pagina può essere inviata ad AnyDoc come pagina `TEXT`,
mentre il contenuto visuale non viene automaticamente passato alla pipeline di
descrizione immagini.

Il risultato può quindi essere un Markdown testualmente corretto ma
semanticamente incompleto.

## Comportamento Attuale

### Pagina `TEXT` con immagine

Quando la pagina contiene abbastanza testo e non supera le soglie di complessità:

1. `pdfplumber` rileva la presenza e l'area dell'immagine.
2. Il router mantiene la pagina come `TEXT`.
3. AnyDoc estrae il testo localmente.
4. Il converter non invoca automaticamente `images.py`.
5. L'immagine può non essere salvata, descritta o rappresentata nel Markdown.
6. Non viene necessariamente prodotta una `ImageRecord` con usage, path e
   descrizione.

Questa è la situazione più rischiosa, perché la pagina viene marcata come
riuscita pur potendo perdere informazione significativa.

### Pagina `COMPLEX` dominata da immagini

Una pagina con poco testo e alta area visuale viene classificata `COMPLEX`.
Viene indirizzata al hard path. Se il `KelpieHardExtractor` non è collegato al
converter principale, la pagina fallisce isolatamente con warning e placeholder.

### Pagina `SCANNED`

Una pagina senza text layer viene classificata `SCANNED`.
AnyDoc non viene chiamato. La pagina deve usare Kelpie per OCR/trascrizione
visuale. Le immagini full-page scansionate non devono essere trattate come

## Cosa È Già Presente

Il modulo image pipeline standalone contiene già i meccanismi necessari per:

- individuare immagini embedded tramite la sorgente PDF;
- renderizzare crop PNG;
- filtrare immagini troppo piccole;
- filtrare aspect ratio estremi;
- calcolare SHA-256;
- deduplicare immagini;
- salvare immagini con nomi deterministici;
- chiamare `VisionBackend.describe_image()`;
- registrare usage e failure;
- costruire figure block inline;
- posizionare il figure block rispetto ai blocchi di pagina;
- escludere immagini full-page delle pagine `SCANNED`;
- usare cache e descrizioni disabilitate in modo esplicito.

Questi comportamenti sono coperti da fake tests. Il limite è che lo stage non è

## Perché È Un Limite Grave

L'assunzione implicita secondo cui una pagina con text layer sia una pagina

Esempi di informazione che può mancare:

- grafici con trend, assi e legenda;
- diagrammi architetturali o di processo;
- screenshot di interfacce o configurazioni;
- formule o annotazioni rasterizzate;
- fotografie di componenti o prodotti;
- tabelle inserite come immagini;
- mappe, schemi e disegni tecnici;
- immagini con etichette che completano il testo circostante.

In questi casi il testo estratto può sembrare completo, ma una sintesi prodotta
a valle perderà relazioni, numeri o evidenze visuali. Il rischio non è solo
una bassa qualità estetica del Markdown: è una perdita di contenuto utile alla
comprensione e alla citazione del documento.

## Impatto Sui Contratti

Il limite attuale ha questi effetti:

- **Markdown:** può contenere il testo ma non il riferimento o la descrizione
  dell'immagine.
- **Sidecar JSON:** può non contenere una `ImageRecord` per un'immagine realmente
  presente nella pagina.
- **Provenance:** il blocco testuale mantiene la pagina originale, ma il
  contenuto visuale non ha una provenance separata.
- **Usage:** non viene consumato o registrato usage Kelpie per la descrizione
  mancante.
- **Cache:** non esiste una cache effettiva per quella descrizione finché lo
  stage immagini non viene eseguito.
- **Quality benchmark:** una pagina `TEXT` può risultare apparentemente riuscita
  anche se il confronto visuale è incompleto.
- **Cutover:** non è corretto usare i risultati attuali per dichiarare qualità
  completa su PDF con figure.

## Cosa Non Succede

Il software non deve:

- attivare automaticamente Firecrawl hosted OCR;
- installare modelli OCR o vision locali;
- inventare una descrizione per un'immagine non analizzata;
- dichiarare `vision` o `anydoc` come metodo di un'immagine che non è stata
  processata;
- trasformare silenziosamente una pagina `TEXT` in una pagina completa solo
  perché il text layer è presente.

Il comportamento attuale è quindi conservativo sul piano della sicurezza e
della tracciabilità, ma incompleto sul piano della copertura visuale.

## Priorità Tecnica

La correzione generale necessaria è collegare l'image stage al loop hybrid per
le pagine digitali eleggibili:

1. ispezionare e classificare la pagina;
2. estrarre il testo con AnyDoc se la pagina è `TEXT`;
3. individuare le immagini embedded della stessa pagina;
4. applicare filtro e dedupe;
5. descrivere le immagini mantenendo il contratto `VisionBackend`;
6. salvare immagini e descrizioni in modo deterministico;
7. inserire i figure block dopo il blocco precedente corretto;
8. registrare `ImageRecord` nel sidecar documentale e usage, latency, cache,
   failure e call record `describe_image` in `run.json`;
9. lasciare le immagini full-page `SCANNED` al hard path senza doppio conteggio.

Il collegamento deve rimanere generale e configurabile. Non deve contenere
regole basate su filename, numero pagina, nome immagine o documento specifico.

## Mitigazione Temporanea

Fino al collegamento completo:

- usare AnyDoc per pagine `TEXT` principalmente testuali;
- considerare non affidabili i risultati di pagine con immagini informative;
- usare il hard path Kelpie per pagine visualmente complesse quando disponibile;
- trattare i failure placeholder come dati mancanti, non come contenuto vuoto;
- non dichiarare il cutover enterprise completo per corpus image-heavy;
- mantenere il fallback e la configurazione di rollback.

## Stato Della Valutazione

La limitazione è stata osservata durante la revisione dell'architettura e del
codice pre-integrazione: image extraction/filtering era presente come componente
testato, ma non era ancora integrato nel normale `PdfConverter` per le pagine
`TEXT`.

Di conseguenza:

- il percorso testo-only è utilizzabile;
- il percorso immagini standalone è verificato con fake backend;
- la copertura end-to-end delle immagini nelle pagine `TEXT` era ancora aperta
  prima dell'enhancement;
- i benchmark attuali non devono essere interpretati come prova di qualità
  visuale completa.

## Stato Dopo L'Integrazione Image-Context

L'integrazione offline è stata completata e verificata con fixture sintetiche:

- le pagine `TEXT` conservano testo, figure, `ImageRecord`, asset e provenance;
- le pagine `COMPLEX` mantengono il risultato hard e possono aggiungere figure
  embedded distinte;
- le pagine `SCANNED` non inviano la stessa immagine full-page a
  `describe_image()`;
- cache, usage, latenza, failure e determinismo sono verificati senza rete.

La verifica Kelpie reale e la regressione sul corpus autorizzato restano
opzionali e dipendono dall'ambiente. Finché non vengono eseguite, non si dichiara
un cutover enterprise completo e il fallback `pdfplumber` resta esplicito.

Nel contratto finale, i dati completi delle immagini appartengono al sidecar
documentale. `run.json` contiene solo i call record `describe_image` e i totali
derivati di usage, latenza e cache; non duplica la lista `ImageRecord`.

## Stato Dopo Il Ciclo Correttivo Post-Trial

I difetti generali osservati nel trial sono stati chiusi offline:

- il percorso pubblico API/CLI costruisce gli adapter immagine e hard configurati;
- i prompt non-secret sono inclusi nel wheel e risolti come risorse del package;
- figure nello stesso vertical band mantengono l'ordine sorgente;
- sidecar freddo e warm-cache sono byte-identici, mentre `run.json` conserva la
  telemetria operativa di cache e chiamate.

Il wheel installato è stato verificato in un ambiente disposable isolato. Il
controllo rappresentativo del comando pubblico ha usato solo PDF autorizzati in
lettura e ha scritto gli output esclusivamente nell'area temporanea approvata;
con AnyDoc e Kelpie non configurati, i fallimenti sono rimasti isolati per pagina.
La guardia aggregata sul percorso autorizzato è passata senza conservare nomi,
estratti, risposte, credenziali o token.

La disponibilità reale di Kelpie resta una limitazione di ambiente: senza il
servizio approvato le chiamate reali sono saltate e non viene attivato alcun OCR
hosted o modello locale. Non si dichiara il cutover enterprise completo; il
fallback `pdfplumber` resta esplicito e opt-in.
