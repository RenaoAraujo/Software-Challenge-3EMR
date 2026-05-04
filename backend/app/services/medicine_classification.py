"""Classificação heurística de medicamentos por classe terapêutica.

Como as OS armazenam medicamentos como strings livres (ex.: "Losartana 50 mg — 120 comp."),
usamos um mapa de palavras-chave (princípio ativo / nome) para inferir a classe.
Qualquer item sem correspondência cai em "Outros".

Este módulo é intencionalmente pequeno e independente para facilitar manutenção
(novos medicamentos podem ser adicionados sem tocar no restante do código).
"""

from __future__ import annotations

import random
import unicodedata

# Ordem importa: a primeira classe cuja palavra-chave for encontrada vence.
# Mantemos a ordem do mais específico para o mais geral.
_MEDICINE_CLASS_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Cardiológica",
        (
            "losartana",
            "valsartana",
            "olmesartana",
            "atorvastatina",
            "sinvastatina",
            "rosuvastatina",
            "aas",
            "acido acetilsalicilico",
            "clopidogrel",
            "ticagrelor",
            "carvedilol",
            "bisoprolol",
            "metoprolol",
            "propranolol",
            "atenolol",
            "enalapril",
            "captopril",
            "lisinopril",
            "amiodarona",
            "digoxina",
            "furosemida",
            "hidroclorotiazida",
            "espironolactona",
            "anlodipino",
            "nifedipino",
            "verapamil",
            "diltiazem",
            "varfarina",
            "rivaroxabana",
            "apixabana",
            "dabigatrana",
        ),
    ),
    (
        "Oncológica",
        (
            "cisplatina",
            "carboplatina",
            "oxaliplatina",
            "doxorrubicina",
            "ciclofosfamida",
            "paclitaxel",
            "docetaxel",
            "fluorouracil",
            "tamoxifeno",
            "anastrozol",
            "letrozol",
            "gencitabina",
            "vincristina",
            "vimblastina",
            "imatinibe",
            "rituximabe",
            "trastuzumabe",
            "bevacizumabe",
            "ondansetrona",
            "granisetrona",
        ),
    ),
    (
        "Antibiótica",
        (
            "amoxicilina",
            "ampicilina",
            "penicilina",
            "piperacilina",
            "tazobactam",
            "cefalexina",
            "cefazolina",
            "ceftriaxona",
            "cefepime",
            "ceftazidima",
            "meropen",
            "ertapeném",
            "imipeném",
            "vancomicina",
            "teicoplanina",
            "linezolida",
            "ciprofloxacino",
            "levofloxacino",
            "moxifloxacino",
            "azitromicina",
            "claritromicina",
            "clindamicina",
            "metronidazol",
            "sulfametoxazol",
            "trimetoprima",
            "gentamicina",
            "amicacina",
            "doxiciclina",
            "tigeciclina",
        ),
    ),
    (
        "Corticoide",
        (
            "dexametasona",
            "prednisona",
            "prednisolona",
            "hidrocortisona",
            "metilprednisolona",
            "betametasona",
            "budesonida",
            "fluticasona",
        ),
    ),
    (
        "Analgésica / Anti-inflamatória",
        (
            "dipirona",
            "paracetamol",
            "ibuprofeno",
            "cetoprofeno",
            "diclofenaco",
            "nimesulida",
            "celecoxibe",
            "etoricoxibe",
            "tramadol",
            "codeina",
            "morfina",
            "fentanila",
            "oxicodona",
        ),
    ),
    (
        "Urológica",
        (
            "tansulosina",
            "alfuzosina",
            "doxazosina",
            "finasterida",
            "dutasterida",
            "sildenafila",
            "tadalafila",
            "vardenafila",
            "oxibutinina",
            "solifenacina",
            "tolterodina",
            "mirabegrona",
        ),
    ),
    (
        "Reumatológica",
        (
            "metotrexato",
            "leflunomida",
            "hidroxicloroquina",
            "sulfassalazina",
            "colchicina",
            "alopurinol",
            "adalimumabe",
            "etanercepte",
            "infliximabe",
            "tofacitinibe",
            "baricitinibe",
        ),
    ),
    (
        "Ortopédica",
        (
            "glucosamina",
            "condroitina",
            "alendronato",
            "risedronato",
            "ibandronato",
            "zoledronico",
            "calcitonina",
            "teriparatida",
            "denosumabe",
            "acido hialuronico",
            "hialuronato",
        ),
    ),
    (
        "Psiquiátrica",
        (
            "sertralina",
            "fluoxetina",
            "paroxetina",
            "escitalopram",
            "citalopram",
            "venlafaxina",
            "duloxetina",
            "amitriptilina",
            "nortriptilina",
            "bupropiona",
            "clonazepam",
            "diazepam",
            "alprazolam",
            "lorazepam",
            "midazolam",
            "risperidona",
            "olanzapina",
            "quetiapina",
            "aripiprazol",
            "lítio",
            "litio",
            "valproato",
            "lamotrigina",
        ),
    ),
    (
        "Endocrinológica",
        (
            "insulina",
            "metformina",
            "glibenclamida",
            "gliclazida",
            "glimepirida",
            "empagliflozina",
            "dapagliflozina",
            "canagliflozina",
            "liraglutida",
            "semaglutida",
            "sitagliptina",
            "linagliptina",
            "levotiroxina",
            "tiroxina",
            "propiltiouracil",
            "metimazol",
        ),
    ),
    (
        "Gastrointestinal",
        (
            "omeprazol",
            "pantoprazol",
            "esomeprazol",
            "lansoprazol",
            "ranitidina",
            "famotidina",
            "domperidona",
            "bromoprida",
            "metoclopramida",
            "simeticona",
            "loperamida",
            "mesalazina",
        ),
    ),
    (
        "Respiratória",
        (
            "salbutamol",
            "formoterol",
            "salmeterol",
            "beclometasona",
            "montelucaste",
            "ipratropio",
            "tiotropio",
            "ambroxol",
            "acetilcisteina",
        ),
    ),
    (
        "Anticoagulante / Antitrombótica",
        (
            "heparina",
            "enoxaparina",
            "dalteparina",
            "fondaparinux",
        ),
    ),
)

_OUTROS = "Outros"


def _normalize(text: str) -> str:
    """Remove acentos, passa para minúsculas e troca não-alfanuméricos por espaço."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text).lower()
    no_accent = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return "".join(ch if ch.isalnum() else " " for ch in no_accent)


def classify_medicine(raw: str) -> str:
    """Devolve o nome da classe terapêutica inferida do texto, ou 'Outros' se nada casar."""
    hay = _normalize(raw)
    if not hay:
        return _OUTROS
    for classe, keywords in _MEDICINE_CLASS_KEYWORDS:
        for kw in keywords:
            if kw in hay:
                return classe
    return _OUTROS


def classes_count() -> int:
    """Número de classes conhecidas (sem 'Outros'). Útil para testes/metadados."""
    return len(_MEDICINE_CLASS_KEYWORDS)


def _keywords_for_class(target: str) -> tuple[str, ...]:
    """Devolve a tupla de palavras-chave da classe (case-insensitive). Vazia se a classe não existe."""
    t = target.strip().lower()
    for classe, keywords in _MEDICINE_CLASS_KEYWORDS:
        if classe.lower() == t:
            return keywords
    return ()


def random_medicines_for_classes(
    allowed_classes: tuple[str, ...],
    quantidade: int,
    *,
    rng: random.Random | None = None,
) -> list[str]:
    """Gera `quantidade` nomes de remédio sorteando uniformemente entre as classes informadas.

    Cada item retornado é uma string capitalizada (princípio ativo) seguida de um sufixo "#N"
    para garantir que o JSON da OS não tenha entradas idênticas. O substring do princípio ativo
    é o que permite ao `classify_medicine` reconhecer a classe corretamente.

    Se nenhuma classe permitida tiver palavras-chave conhecidas, faz fallback para
    "Medicamento (teste) N" (mantém o comportamento legado).
    """
    rg = rng or random
    pools: list[tuple[str, tuple[str, ...]]] = [
        (c, _keywords_for_class(c)) for c in allowed_classes
    ]
    pools = [(c, kws) for c, kws in pools if kws]
    if not pools:
        return [f"Medicamento (teste) {i + 1}" for i in range(max(0, int(quantidade)))]
    items: list[str] = []
    for i in range(max(0, int(quantidade))):
        _, kws = rg.choice(pools)
        kw = rg.choice(kws)
        items.append(f"{kw.capitalize()} #{i + 1}")
    return items
