# README_AT — Registro Modifiche Adaptronics

Questo file traccia tutte le modifiche apportate al fork Adaptronics di LabRecorder
rispetto al repository originale (upstream): https://github.com/labstreaminglayer/App-LabRecorder

Ogni modifica è contrassegnata nel codice con il commento `[ADAPTRONICS]`.

---

## Obiettivo del fork

Adattare LabRecorder a un contesto di test industriale su patch.
Le modifiche principali riguardano:
- Struttura cartelle: `ID_CAD / ID_Patch / run_001.xdf`
- Pannello metadati aggiuntivo (Operator, Material ID, Test ID, Note, gruppo Perno)
- Metadati scritti nella FileHeader XDF nel blocco `<adaptronics>`
- Menu a tendina cascata popolati da CSV (`LabRecorder_AT.csv`)
- Adattamento dell'interfaccia grafica al workflow degli operatori

---

## Modifiche effettuate

### 1. `src/mainwindow.ui` — Etichette rinominate e widget nascosti

**Cosa:** rinominati i testi delle etichette dei campi esistenti e nascosti quelli non rilevanti.

| Campo originale | Nuovo nome | Segnaposto | Stato |
|----------------|------------|------------|-------|
| Acq. | ID CAD | `%a` | visibile |
| Session | — | `%s` | **nascosto** (si sovrappone a ID CAD) |
| Participant | ID Patch | `%p` | visibile |
| Counter | Run | `%n` | visibile |
| Block/Task | — | `%b` | nascosto |
| Modality | — | `%m` | nascosto |
| BIDS checkbox | — | — | nascosto |

**Perché:** adattare la terminologia all'uso industriale. Production Code rimosso
perché identico a ID CAD. I widget sono nascosti con `visible=false`, NON rimossi:
il codice C++ che li referenzia continua a compilare senza errori.

**Conflitti futuri:** se l'upstream modifica queste label, il conflitto è visibile.
Mantenere i nuovi nomi e le proprietà `visible=false`.

---

### 2. `src/mainwindow.ui` — Campi convertiti da QLineEdit a QComboBox editabile

**Cosa:** i campi `lineEdit_acq` e `lineEdit_participant` sono stati
convertiti da `QLineEdit` a `QComboBox` con proprietà `editable = true`.
(Anche `lineEdit_session` è QComboBox, ma ora nascosto.)

**Perché:** permette all'operatore di scegliere da un menu a tendina (popolato da CSV)
oppure di digitare liberamente un valore non presente nella lista.

**File C++ collegato:** vedere modifica 4 (`src/mainwindow.cpp`).

**Conflitti futuri:** se l'upstream modifica questi widget, mantenere il tipo `QComboBox`
e la proprietà `editable = true`.

---

### 3. `src/mainwindow.ui` — Pannello metadati sessione (colonna destra)

**Cosa:** aggiunto un `QGroupBox` "Metadati Sessione" come terza colonna a destra.
Contiene i campi di sessione e il gruppo Perno:

| Widget | Label | Tipo | Valori |
|--------|-------|------|--------|
| `comboBox_meta_operator` | Operator | QComboBox editabile | CSV TYPE=OPERATOR |
| `comboBox_meta_material` | Material ID | QComboBox editabile | CSV TYPE=MATERIAL |
| `comboBox_meta_test` | Test ID | QComboBox editabile | CSV TYPE=TEST |
| `plainTextEdit_meta_note` | Note | QPlainTextEdit | testo libero multilinea |
| `comboBox_meta_perno_materiale` | Materiale | QComboBox editabile | CSV PERNO_MATERIALE:CAD |
| `comboBox_meta_perno_diametro` | Diametro | QComboBox editabile | CSV PERNO_DIAMETRO:CAD |
| `comboBox_meta_perno_numero` | N. perni | QComboBox editabile | CSV PERNO_NUMERO:CAD |
| `comboBox_meta_perno_posizione` | Posizione | QComboBox editabile | CSV PERNO_POSIZIONE:CAD |

I 4 campi Perno sono raggruppati in `QGroupBox "Perno"` e dipendono dall'ID CAD selezionato
(cascata: cambio CAD → i dropdown si ripopolano con i figli dichiarati nel CSV).

**Perché:** questi metadati non fanno parte della struttura cartelle ma vengono
scritti nella FileHeader XDF per uso nel pipeline ML/DL.

**Conflitti futuri:** blocco completamente nuovo, nessun elemento esistente toccato.
In caso di conflitto, mantenere i blocchi `<!-- [ADAPTRONICS] ... -->`.

---

### 4. `src/mainwindow.cpp` — Aggiornamenti per QComboBox e cascata CSV

**Cosa A — segnali e accesso ai valori:**
- Segnali: `QLineEdit::editingFinished` → `QComboBox::currentTextChanged`
- Lettura valore: `.text()` → `.currentText()`
- Scrittura valore: `.setText()` → `.setCurrentText()`

Punti toccati: costruttore (connessioni segnali), `replaceFilename()`,
`buildBidsTemplate()`, `rcsUpdateFilename()`.

**Cosa B — cascata ID CAD → ID Patch + 4 campi Perno:**
Nel costruttore, aggiunta connessione lambda:
```cpp
connect(ui->lineEdit_acq, &QComboBox::currentTextChanged, this, [this](const QString &text) {
    ui->lineEdit_participant->clear();
    ui->lineEdit_participant->addItems(atCsvData_["PATCH:" + text]);
    // perno: ripopola in base al CAD selezionato
    repopPerno(ui->comboBox_meta_perno_materiale, "PERNO_MATERIALE");
    repopPerno(ui->comboBox_meta_perno_diametro,  "PERNO_DIAMETRO");
    repopPerno(ui->comboBox_meta_perno_numero,    "PERNO_NUMERO");
    repopPerno(ui->comboBox_meta_perno_posizione, "PERNO_POSIZIONE");
});
```
Quando l'operatore seleziona un ID CAD, ID Patch e i 4 dropdown Perno si ripopolano
automaticamente con i figli del CAD dichiarati nel CSV.

**Cosa C — raccolta metadati e avvio registrazione:**
In `startRecording()`, prima di creare l'oggetto `recording`, tutti i valori
dell'interfaccia vengono raccolti in una `std::map<std::string,std::string>` e
passati al costruttore di `recording` (vedere modifica 6). Campi raccolti:
`cad_id`, `patch_id`, `operator`, `material_id`, `test_id`, `note`,
`perno_materiale`, `perno_diametro`, `perno_numero`, `perno_posizione`.

**Conflitti futuri:** tutto il codice [ADAPTRONICS] è in blocchi separati e delimitati.

---

### 5. `src/mainwindow.h` — Struttura dati CSV e dichiarazione metodo

**Cosa:** aggiunti due membri privati:
```cpp
QMap<QString, QStringList> atCsvData_;   // dati gerarchici del CSV
void loadAtCsv(const QString &cfgDir);   // metodo di caricamento
```

**Conflitti futuri:** blocco nuovo, nessun membro esistente toccato.

---

### 6. `src/recording.h` + `src/recording.cpp` — Parametro metadata

**Cosa:** aggiunto parametro opzionale `metadata` al costruttore di `recording`:
```cpp
recording(const std::string &filename,
          const std::vector<lsl::stream_info> &streams,
          const std::vector<std::string> &watchfor,
          std::map<std::string, int> syncOptions,
          bool collect_offsets = true,
          const std::map<std::string, std::string> &metadata = {}); // [ADAPTRONICS]
```
Nel corpo del costruttore (`recording.cpp`), il parametro viene inoltrato a `XDFWriter`:
```cpp
: file_(filename, metadata), ...
```

**Perché:** la catena di propagazione è:
`mainwindow.cpp` → `recording` → `XDFWriter` → FileHeader XDF.

**Conflitti futuri:** il parametro è opzionale con default `{}`.
Il codice upstream che chiama `recording(...)` senza metadata continua a funzionare.

---

### 7. `xdfwriter/xdfwriter.h` + `xdfwriter/xdfwriter.cpp` — Scrittura metadati nella FileHeader XDF

**Cosa:** il costruttore di `XDFWriter` accetta ora un secondo parametro opzionale:
```cpp
XDFWriter(const std::string &filename,
          const std::map<std::string, std::string> &metadata = {}); // [ADAPTRONICS]
```
Se `metadata` non è vuota, nel blocco `<info>` della FileHeader XDF viene aggiunto:
```xml
<adaptronics>
  <cad_id>91912</cad_id>
  <patch_id>PATCH001</patch_id>
  <operator>Mario Rossi</operator>
  <material_id>acciaio</material_id>
  <test_id>T-001</test_id>
  <note>Nota libera</note>
  <perno_materiale>acciaio</perno_materiale>
  <perno_diametro>M6</perno_diametro>
  <perno_numero>2</perno_numero>
  <perno_posizione>fronte</perno_posizione>
</adaptronics>
```

**Perché:** il blocco `<info>` della FileHeader è il posto standard XDF per i metadati
globali della sessione. Qualsiasi parser XDF (MNE-Python, EEGLAB, strumenti ML/DL custom)
può leggerlo senza conoscere estensioni proprietarie.

**Conflitti futuri:** il parametro è opzionale. Tutta la logica [ADAPTRONICS] è in un
blocco `if (!metadata.empty())` separato dal codice upstream. Non tocca la struttura
dei chunk XDF né il formato dei dati.

---

## Formato file CSV — `LabRecorder_AT.csv`

Il file deve trovarsi nella stessa cartella del `.cfg` (o dell'eseguibile se nessun `.cfg` è specificato).

```
TYPE,ID,PARENT_ID
CAD,91912,
CAD,91913,
PATCH,PATCH001,91912
PATCH,PATCH002,91912
PATCH,PATCH003,91913
MATERIAL,acciaio,
MATERIAL,alluminio,
OPERATOR,Mario Rossi,
OPERATOR,Anna Bianchi,
TEST,T-001,
TEST,T-002,
PERNO_MATERIALE,acciaio,91912
PERNO_MATERIALE,titanio,91912
PERNO_DIAMETRO,M6,91912
PERNO_DIAMETRO,M8,91912
PERNO_NUMERO,1,91912
PERNO_NUMERO,2,91912
PERNO_POSIZIONE,fronte,91912
PERNO_POSIZIONE,retro,91912
```

- `PATCH` usa come `PARENT_ID` il codice `CAD` direttamente
- `MATERIAL`, `OPERATOR`, `TEST` non hanno gerarchia (PARENT_ID vuoto)
- `PERNO_MATERIALE`, `PERNO_DIAMETRO`, `PERNO_NUMERO`, `PERNO_POSIZIONE` usano il codice `CAD` come `PARENT_ID`
  → i dropdown Perno si aggiornano automaticamente quando si seleziona un ID CAD

---

## Note generali

- Le modifiche sono progettate per minimizzare i conflitti con l'upstream.
- Ogni modifica al codice C++ è marcata con `// [ADAPTRONICS] BEGIN ... // [ADAPTRONICS] END`.
- Ogni modifica all'XML dell'UI è marcata con `<!-- [ADAPTRONICS] ... -->`.
- In caso di merge conflict: mantenere sempre le righe marcate `[ADAPTRONICS]`.
- I widget nascosti NON vengono mai rimossi: il codice C++ che li referenzia continua a compilare.
