#!/usr/bin/env python3
"""Volume rappresentativo per la prova di carico — non dati realistici, dati veri.

    python3 tools/load/popola.py --db nli_test [--partner 50000]

La terza condizione che mancava alla prova di D27, dopo il pool prefork e la latenza
del fornitore: **una banca dati su cui una domanda costi qualcosa**. Con trentasette
partner, `search_read` su `res.partner` torna prima che PostgreSQL abbia finito di
pianificarla, la latenza misurata e' quella del trasporto HTTP, e il degrado sotto
carico non ha modo di manifestarsi — non perche' il prodotto isoli bene, ma perche'
non c'e' niente da isolare.

**Cinquantamila partner non sono un'installazione reale** e questo strumento non lo
pretende: una vera ha anche righe d'ordine, movimenti contabili, allegati e indici
frammentati da anni di scritture. Sono pero' abbastanza perche' la sonda dell'utente
ordinario faccia un lavoro misurabile, che e' l'unica cosa che la prova chiede loro.

Idempotente: conta quanti ce ne sono e crea la differenza. Rieseguirlo non gonfia la
base, e una prova che dipende da quante volte e' stato lanciato lo strumento non e'
una prova.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prova_isolamento import Session  # noqa: E402

CITIES = ("Milano", "Roma", "Torino", "Napoli", "Bologna", "Firenze", "Genova",
          "Palermo", "Bari", "Verona", "Padova", "Trieste")

#: Lotti piccoli: una `create` da cinquantamila righe in una sola chiamata occupa un
#: worker per minuti, e il primo effetto di questo strumento sarebbe far cadere il
#: server che deve poi essere misurato.
BATCH = 500


def seed_partners(session: Session, target: int) -> int:
    existing = session.call_kw("res.partner", "search_count", [[]])
    missing = max(0, target - existing)
    generator = random.Random(42)  # deterministico, come il corpus
    created = 0
    while created < missing:
        size = min(BATCH, missing - created)
        rows = [{
            "name": f"Azienda Prova {existing + created + index:06d}",
            "city": generator.choice(CITIES),
            "is_company": (index % 3) != 0,
            "ref": f"LOAD{existing + created + index:06d}",
        } for index in range(size)]
        session.call_kw("res.partner", "create", [rows])
        created += size
        print(f"    {created}/{missing}", end="\r", flush=True)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8069")
    parser.add_argument("--db", required=True)
    parser.add_argument("--login", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--partner", type=int, default=50_000)
    arguments = parser.parse_args()

    session = Session(arguments.url, arguments.db, arguments.login,
                      arguments.password, timeout=600)
    created = seed_partners(session, arguments.partner)
    total = session.call_kw("res.partner", "search_count", [[]])
    print(f"    creati {created}, totale {total}                    ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
