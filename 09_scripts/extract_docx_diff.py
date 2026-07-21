# -*- coding: utf-8 -*-
import os, json, difflib, sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document

BASE = r"C:\Users\M.Diouf\OneDrive\Bureau\RDC Bulletin V1\Bulletin_rdc_2026_agents"
ORIG_PATH  = os.path.join(BASE, "10_output", "bulletin_relecture_2026-07-21.docx")
MODIF_PATH = os.path.join(BASE, "10_output", u"bulletin_relecture_modifs acc\u00e9pt\u00e9s.docx")
OUT_PATH   = os.path.join(BASE, "10_output", "diff_word_vs_modif.json")

def extract_paragraphs(path):
    doc = Document(path)
    result = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            result.append({"index": i, "style": para.style.name, "text": text})
    return result

print("Lecture originale...")
orig  = extract_paragraphs(ORIG_PATH)
print(f"  -> {len(orig)} paragraphes")
print("Lecture modifiee...")
modif = extract_paragraphs(MODIF_PATH)
print(f"  -> {len(modif)} paragraphes")

orig_texts  = [p["text"] for p in orig]
modif_texts = [p["text"] for p in modif]

matcher = difflib.SequenceMatcher(None, orig_texts, modif_texts, autojunk=False)
opcodes = matcher.get_opcodes()

diffs = []
for tag, i1, i2, j1, j2 in opcodes:
    if tag == "equal":
        continue
    diffs.append({
        "op": tag,
        "orig_range": [i1, i2],
        "modif_range": [j1, j2],
        "orig_texts": orig_texts[i1:i2],
        "modif_texts": modif_texts[j1:j2],
    })

print(f"\n{len(diffs)} blocs de differences detectes.")

for d in diffs:
    op = d["op"]
    if op == "replace":
        for ot, nt in zip(d["orig_texts"], d["modif_texts"]):
            if ot != nt:
                print(f"\n[REPLACE]\n  - {ot[:150]}\n  + {nt[:150]}")
    elif op == "insert":
        for t in d["modif_texts"]:
            print(f"\n[INSERT]\n  + {t[:150]}")
    elif op == "delete":
        for t in d["orig_texts"]:
            print(f"\n[DELETE]\n  - {t[:150]}")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(diffs, f, ensure_ascii=False, indent=2)
print(f"\nDiff sauvegarde: {OUT_PATH}")