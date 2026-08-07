#!/usr/bin/env bash
# La corsa sulla macchina affittata, dall'inizio alla fine.
#
#   ./tools/finetuning/corri.sh fumo      # 500 esempi su A6000, ~$2, verifica la catena
#   ./tools/finetuning/corri.sh 4b        # la corsa vera sul candidato principale
#   ./tools/finetuning/corri.sh 2b        # l'obiettivo ambizioso di ai/19 §5
#   ./tools/finetuning/corri.sh 9b        # la riserva, solo se gli altri due non passano
#
# **Il dataset e' lo stesso per tutte e tre.** Nulla in un esempio dipende dalla
# taglia, e le tre Qwen 3.5 condividono tokenizzatore e schema di conversazione: e'
# la ragione per cui cambiare candidato costa una riga invece di un progetto.
#
# Perche' uno script e non tre comandi a mano: la fatturazione di RunPod e' **al
# secondo**, e premia la disciplina di preparare tutto in locale, caricare, correre,
# scaricare, spegnere. Ogni minuto passato a ricordarsi il comando successivo e' un
# minuto pagato.
#
# Cosa NON fa: non affitta la macchina e non spegne niente. Accendere e spegnere una
# macchina che costa e' una decisione di chi paga, non di uno script.

set -euo pipefail

QUALE="${1:?Usage: corri.sh fumo|4b|2b}"
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$RADICE"

case "$QUALE" in
  fumo) RICETTA=tools/finetuning/ricette/aida-4b-lora.yml; USCITA=out/aida-4b-lora ;;
  4b)   RICETTA=tools/finetuning/ricette/aida-4b-lora.yml; USCITA=out/aida-4b-lora ;;
  2b)   RICETTA=tools/finetuning/ricette/aida-2b-lora.yml; USCITA=out/aida-2b-lora ;;
  9b)   RICETTA=tools/finetuning/ricette/aida-9b-lora.yml; USCITA=out/aida-9b-lora ;;
  *)    echo "non conosco '$QUALE': usa fumo, 4b, 2b o 9b" >&2; exit 2 ;;
esac

echo "== 1. il dataset =="
# Il dataset non viaggia col repository: si rigenera dall'atlante con lo stesso seme,
# quindi la macchina affittata lo ricostruisce identico invece di scaricarlo.
if [ "$QUALE" = "fumo" ]; then
  # Cinquecento esempi non possono contenere il minimo di cinquanta per simbolo —
  # ventidue operazioni per cinquanta fanno gia' millecento. La prova di fumo non
  # misura la copertura: verifica che la catena intera giri.
  python3 tools/finetuning/genera_dataset.py --genera 4000 --bersaglio 500 --minimo 5
else
  python3 tools/finetuning/genera_dataset.py --genera 40000 --bersaglio 10000
fi
echo
sed -n '1,40p' data/copertura.txt

echo "== 2. il controllo che fallisce in trenta secondi invece che dopo un'ora =="
# I nomi dei campi di axolotl sono cambiati piu' volte fra una versione e l'altra.
# `preprocess` legge la ricetta e i dati e si ferma subito se qualcosa non torna: e'
# la ragione per cui questo passo esiste separato dal successivo.
axolotl preprocess "$RICETTA"

echo "== 3. l'addestramento =="
axolotl train "$RICETTA"

echo "== 4. da adapter a GGUF =="
# L'adapter **non si fonde** nel modello base (ai/18 §6): si misurano base e affinato
# fianco a fianco sullo stesso ollama, e si torna indietro togliendo una riga.
python3 llama.cpp/convert_lora_to_gguf.py \
  --base "$(grep '^base_model:' "$RICETTA" | awk '{print $2}')" \
  "$USCITA" --outfile "$USCITA/adapter.gguf"

echo
echo "Fatto. Scarica $USCITA/adapter.gguf, poi in locale:"
# La base la dice la ricetta, non un valore scritto a mano: un adapter attaccato alla
# taglia sbagliata e' un guasto che non si annuncia.
TAGLIA="$(grep '^base_model:' "$RICETTA" | sed 's#.*Qwen3.5-\([0-9]*B\).*#\1#' | tr 'A-Z' 'a-z')"
echo "  printf 'FROM qwen3.5:${TAGLIA}\\nADAPTER ./adapter.gguf\\n' > Modelfile"
echo "  ollama create aida-dsl-${TAGLIA} -f Modelfile"
echo
echo "E poi il cancello di ai/18 §9, che decide da solo:"
echo "  NLI_ALLOWED_HOSTS=127.0.0.1:11434 python3 ai/corpus/misura_accuratezza.py \\"
echo "    --endpoint http://127.0.0.1:11434/v1 --profilo aida-dsl \\"
echo "    --vincolata --ragionamento none --finestra 8192 --casi 444 --attesa 300"
echo
echo "La linea di partenza da battere: 74,6% su 414 aperture (00 §48.7)."
echo "Spegni la macchina."
