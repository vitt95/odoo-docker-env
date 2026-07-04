# ARCHITECTURE.md

## Obiettivo

Costruire una Premium UI mantenendo Odoo come backend.

Il redesign deve essere progressivo.

La compatibilità con Odoo ha priorità assoluta.

---

# Architettura

Odoo Core

↓

Theme Engine

↓

Classic Skin

Premium Skin

---

# Strategia

Il progetto NON sostituisce Odoo.

Il progetto costruisce un layer di presentazione sopra Odoo.

---

# Regole

Non modificare direttamente il core.

Preferire:

* inheritance
* patch minime
* asset dedicati
* override SCSS

---

# HTML

Quando possibile mantenere:

* struttura HTML
* classi Odoo
* data attributes

Le classi esistenti possono essere utilizzate dal codice JavaScript.

Sono quindi considerate parte del contratto applicativo.

---

# CSS

Preferire:

CSS Variables

SCSS

Componenti

Design Tokens

Evitare CSS globale quando possibile.

---

# JavaScript

Patch solo se realmente necessario.

Prima verificare se il risultato può essere ottenuto tramite:

* CSS
* Template
* OWL composition

---

# Asset

Separare chiaramente:

Theme

Componenti

Layout

Views

Pages

---

# Roadmap tecnica

1. Discovery
2. Theme Engine
3. Design Tokens
4. Typography
5. Spacing
6. Component Library
7. Motion
8. Layout
9. Login
10. Navbar
11. Sidebar
12. Dashboard
13. Form View
14. List View
15. Kanban
16. Calendar
17. Chatter
18. Dialog
19. Ottimizzazione
20. QA finale

Ogni fase deve lasciare il progetto funzionante.
