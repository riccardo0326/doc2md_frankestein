# IMPORTANTE

## Phase 0 approvata

Il sign-off umano `go` e' stato ricevuto il 2026-10-27.

- La licenza Rust di `ryu 1.0.23` (`Apache-2.0 OR BSL-1.0`) e' approvata per
  questo progetto usando l'opzione Apache-2.0.
- AnyDoc resta locale e opzionale: non deve mai attivare Firecrawl hosted OCR.
- Nessun task successivo o adapter di produzione e' stato avviato in questa
  sessione.

## Slicing PDF deciso

- Usare `pypdf` con `PdfReader`/`PdfWriter.add_page()` e `BytesIO` per creare il
  PDF di una pagina in memoria.
- Conservare sempre il numero di pagina originale fuori da AnyDoc; la pagina
  nel PDF ritagliato diventa pagina 1.
- Passare ad AnyDoc solo pagine con testo estraibile.
- Pagine vuote o image-based non devono essere interpretate come autorizzazione
  a usare OCR hosted: restano sul percorso Kelpie/fallback configurato o come
  errore isolato.
- Il test sui 6 PDF in `C:\Users\rp99480\dev\doc2md\samples\unstructured-demo`
  ha confermato che lo slicing funziona per le pagine testuali e per le pagine
  con immagini che conservano un text layer.

Dettagli, risultati per pagina e limiti sono in `docs/discovery.md`; decisioni
formali in `docs/decisions.md`.
