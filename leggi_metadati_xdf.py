"""
Legge la FileHeader di un file XDF e mostra i metadati Adaptronics.
Uso: python leggi_metadati_xdf.py "percorso\file.xdf"
"""
import struct

def leggi_vli(f):
    """Legge un intero a lunghezza variabile dal formato XDF."""
    n = struct.unpack('B', f.read(1))[0]
    if n == 1:
        return struct.unpack('B', f.read(1))[0]
    elif n == 4:
        return struct.unpack('<I', f.read(4))[0]
    elif n == 8:
        return struct.unpack('<Q', f.read(8))[0]
    else:
        raise ValueError(f"VLI non valido: primo byte = {n}")

def leggi_fileheader(percorso):
    with open(percorso, 'rb') as f:
        # Controlla il magic code XDF
        magic = f.read(4)
        if magic != b'XDF:':
            print("ERRORE: il file non è un XDF valido (magic code mancante).")
            return

        # Il primo chunk deve essere la FileHeader (tag = 1)
        chunk_len = leggi_vli(f)
        tag = struct.unpack('<H', f.read(2))[0]

        if tag != 1:
            print(f"ERRORE: il primo chunk non è una FileHeader (tag trovato: {tag})")
            return

        # Legge il contenuto XML della FileHeader
        content_len = chunk_len - 2  # sottraiamo i 2 byte del tag
        content = f.read(content_len).decode('utf-8', errors='replace')

        print("=" * 60)
        print("FILEHEADER XML:")
        print("=" * 60)
        print(content)
        print("=" * 60)

        # Verifica presenza metadati Adaptronics
        if '<adaptronics>' in content:
            print("\n✓ Metadati Adaptronics trovati!\n")
            # Estrae e stampa solo il blocco <adaptronics>
            start = content.find('<adaptronics>')
            end   = content.find('</adaptronics>') + len('</adaptronics>')
            print(content[start:end])
        else:
            print("\n✗ Metadati Adaptronics NON trovati.")
            print("  Probabilmente è un file registrato con la versione precedente.")

# Modifica questo percorso con il tuo file XDF
PERCORSO_XDF = r"C:\Registrazioni\Adaptronics\91912ww\run_001.xdf"

print(f"File: {PERCORSO_XDF}\n")
leggi_fileheader(PERCORSO_XDF)
