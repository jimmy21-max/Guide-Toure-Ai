import difflib
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer

PROJECT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_DIR / "config.json"
STORE_DIR = PROJECT_DIR / "data" / "vector_store"
ENTITIES_PATH = (
    PROJECT_DIR / "data" / "processed" / "rdb_tourism_entities_enriched.csv"
)

LLM_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
LLM_DIR = PROJECT_DIR / "models" / "qwen2.5-0.5b-instruct"
EMBEDDING_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ---- Settings (explained in the report) ----
TOP_K = 3                 # documents given to the model for law questions
LEXICAL_WEIGHT = 0.15     # bonus for documents containing the question's words
MAX_NEW_TOKENS = 120      # maximum answer length
MAX_CONTEXT_CHARS = 600   # each document is cut to this length in the prompt
REFUSAL_THRESHOLD = 0.40  # below this best score, the question is out of scope
FUZZY_CUTOFF = 0.82       # how similar a misspelled word must be to be corrected
LIST_LIMIT = 15           # how many names a list answer shows

REFUSAL_TEXT = "I could not find this in the documents."

STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "shall", "may", "can",
    "what", "who", "when", "how", "are", "was", "any", "all", "from",
    "has", "have", "does", "not", "its", "their", "which", "where",
    "should", "must", "will", "than", "then", "there", "about", "tell",
    "list", "give",
}


def tokenize(text):
    tokens = []
    for word in re.findall(r"[a-z]+", text.lower()):
        if len(word) <= 2 or word in STOP_WORDS:
            continue
        if word.endswith("s") and len(word) > 3:
            word = word[:-1]
        tokens.append(word)
    return tokens


# ---------- Load everything from local folders ----------
config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
embedding_dir = Path(config["embedding_model_folder"].replace("\\", "/"))
if not embedding_dir.is_absolute():
    embedding_dir = PROJECT_DIR / embedding_dir
embedder = SentenceTransformer(
    str(embedding_dir) if embedding_dir.is_dir() else EMBEDDING_NAME
)
embeddings = np.load(STORE_DIR / "embeddings.npy")
documents = json.loads((STORE_DIR / "documents.json").read_text(encoding="utf-8"))
document_tokens = [set(tokenize(d["ref"] + " " + d["text"])) for d in documents]

if LLM_DIR.exists():
    print("Loading language model from local folder...")
    tokenizer = AutoTokenizer.from_pretrained(str(LLM_DIR))
    llm = AutoModelForCausalLM.from_pretrained(str(LLM_DIR))
else:
    print(f"Loading language model from Hugging Face: {LLM_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(LLM_NAME)
    llm = AutoModelForCausalLM.from_pretrained(LLM_NAME)
llm.eval()


def retrieve(question, k=None):
    k = k or TOP_K
    query_vector = embedder.encode([question], normalize_embeddings=True)[0]
    similarity = embeddings @ query_vector

    query_words = set(tokenize(question))
    if query_words:
        keyword = np.array([
            len(query_words & tokens) / len(query_words)
            for tokens in document_tokens
        ])
    else:
        keyword = np.zeros(len(documents))

    final_score = similarity + LEXICAL_WEIGHT * keyword
    best = np.argsort(final_score)[::-1][:k]
    return [(documents[i], float(final_score[i])) for i in best]


# =====================================================================
# Entity data (used by the fast paths: no language model needed)
# =====================================================================
entities = pd.read_csv(ENTITIES_PATH, dtype=str).fillna("")
records = entities.to_dict("records")

# Words that appear in many business names; they do not identify one business
GENERIC = {
    "hotel", "hotels", "ltd", "limited", "lodge", "resort", "company", "co",
    "inc", "and", "the", "of", "tours", "tour", "travel", "safaris", "safari",
    "restaurant", "bar", "apartments", "apartment", "guest", "house", "agency",
    "services", "group", "motel", "residence", "villa", "cafe", "plc", "sarl",
    "rwanda",
}

INTENT_WORDS = {
    "rooms": {"room", "rooms"},
    "beds": {"bed", "beds"},
    "phone": {"phone", "telephone", "tel", "call", "mobile"},
    "email": {"email", "emails", "mail"},
    "website": {"website", "web", "site", "url", "link"},
    "cuisine": {"cuisine", "food", "menu", "serve", "serves", "dishes"},
    "location": {"where", "located", "location", "district", "province",
                 "address", "situated"},
    "status": {"licensed", "licence", "license", "licenced", "status"},
    "contact": {"contact", "contacts"},
    "about": {"about", "details", "detail", "information", "info",
              "describe", "description", "tell"},
}

LIST_WORDS = {"which", "list", "all", "every", "any", "near", "nearby",
              "best", "many"}

# Words that mean the question is about the law, not about a business
LAW_WORDS = {"license", "licenses", "licence", "suspend", "suspension",
             "cancel", "cancellation", "board", "law", "article", "fine",
             "fines", "levy", "grading", "grade", "transfer", "valid",
             "validity"}

COMMON_WORDS = {
    "what", "when", "does", "have", "with", "from", "this", "that", "there",
    "their", "many", "much", "give", "show", "find", "please", "number",
    "long", "valid", "board", "operating",
}
NO_CORRECTION = (set().union(*INTENT_WORDS.values()) | GENERIC | LIST_WORDS
                 | COMMON_WORDS)

# Words ignored when checking a list question
FILLER = (STOP_WORDS | LIST_WORDS | {
    "in", "is", "of", "at", "me", "you", "a", "an", "to", "located",
    "situated", "there", "name", "names", "find", "show", "many", "how",
    "are", "do", "does", "please", "i", "we", "my", "our", "it", "or",
})


def singular(word):
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def name_words(name):
    return re.findall(r"[a-z0-9]+", name.lower())


entity_keys = []
for record in records:
    words = name_words(record["entity_name"])
    key = {w for w in words if w not in GENERIC}
    entity_keys.append(key if key else set(words))

vocabulary = set().union(*entity_keys)
vocabulary_list = sorted(vocabulary)

districts = {r["district"].lower() for r in records}
province_words = {}
for province in {r["province"].lower() for r in records}:
    for w in re.findall(r"[a-z]+", province):
        if w not in {"province", "city", "of"}:
            province_words[w] = province

type_tokens = set()
for r in records:
    type_tokens |= set(re.findall(
        r"[a-z]+", (r["sub_category"] + " " + r["category"]).lower()))


def clean_website(value):
    match = re.search(
        r"(?:https?://)?(?:www\.)?[\w\-]+(?:\.[\w\-]+)+(?:/[^\s\[\]()]*)?", value)
    if not match:
        return ""
    website = match.group(0)
    if website.startswith(("http://", "https://")):
        return website
    return f"https://{website}"


def find_entities(question):
    """Return (scored matches, question words). Misspelled words are corrected."""
    words = re.findall(r"[a-z0-9]+", question.lower())
    corrected = []
    for word in words:
        if word in vocabulary or len(word) < 4 or word in NO_CORRECTION:
            corrected.append(word)
        else:
            close = difflib.get_close_matches(
                word, vocabulary_list, n=1, cutoff=FUZZY_CUTOFF)
            corrected.append(close[0] if close else word)

    question_set = set(corrected)
    scored = []
    for index, key in enumerate(entity_keys):
        if not key:
            continue
        hits = key & question_set
        if hits:
            scored.append((len(hits) / len(key), len(hits), index))
    scored.sort(key=lambda s: (-s[0], -s[1], s[2]))
    return scored, words


def detect_intents(words):
    word_set = set(words)
    return [name for name, group in INTENT_WORDS.items() if word_set & group]


def is_guide(record):
    return "guide" in record["sub_category"].lower()


def entity_details(record):
    rooms = record["Number of Rooms"]
    beds = record["Number of beds"]
    room_count = rooms if rooms not in ("", "0") else "Not listed"
    bed_count = beds if beds not in ("", "0") else "Not listed"
    details = [
        ("Category", record["category"] or "Not listed"),
        ("Type", record["sub_category"] or "Not listed"),
        ("District", record["district"] or "Not listed"),
        ("Province", record["province"] or "Not listed"),
        ("Licence status", record["status"] or "Not listed"),
        ("Rooms", room_count),
        ("Beds", bed_count),
        ("Cuisine", record["Cuisine"] or "Not listed"),
    ]
    if is_guide(record):
        details.append(("Contact", "Individual tour-guide contact details are not shown"))
    else:
        details.append(("Phone", record["Phone"] or "Not listed"))
        details.append(("Email", record["Email"] or "Not listed"))
    return details


def entity_table_row(record):
    rooms = record["Number of Rooms"]
    beds = record["Number of beds"]
    row = {
        "Business": record["entity_name"],
        "Category": record["category"] or "Not listed",
        "Type": record["sub_category"] or "Not listed",
        "District": record["district"] or "Not listed",
        "Province": record["province"] or "Not listed",
        "Licence status": record["status"] or "Not listed",
        "Rooms": rooms if rooms not in ("", "0") else "Not listed",
        "Beds": beds if beds not in ("", "0") else "Not listed",
        "Cuisine": record["Cuisine"] or "Not listed",
        "Phone": "Not shown" if is_guide(record) else record["Phone"] or "Not listed",
        "Email": "Not shown" if is_guide(record) else record["Email"] or "Not listed",
        "Website": "" if is_guide(record) else clean_website(record["Website"]),
        "RDB profile": record["profile_url"].strip(),
    }
    return row


def entity_answer(record):
    links = []
    if not is_guide(record):
        website = clean_website(record["Website"])
        if website:
            links.append({"label": "Open business website", "url": website})
    profile_url = record["profile_url"].strip()
    if profile_url:
        links.append({"label": "Open official RDB profile", "url": profile_url})
    return {
        "kind": "entity",
        "name": record["entity_name"],
        "details": entity_details(record),
        "links": links,
    }


# ---------- Fast path 1: list questions answered by filtering the data ----------
def list_answer(words):
    plural_type = any(w.endswith("s") and singular(w) in type_tokens for w in words)
    if not (set(words) & LIST_WORDS or plural_type):
        return None
    if set(words) & LAW_WORDS:
        return None

    area_districts = []
    area_provinces = []
    type_words = []
    for w in words:
        if w in FILLER:
            continue
        if w in districts:
            area_districts.append(w)
        elif w in province_words:
            area_provinces.append(province_words[w])
        elif singular(w) in type_tokens:
            type_words.append(singular(w))
        else:
            return None   # a word we cannot explain: leave it to the other paths

    if not (area_districts or area_provinces) or not type_words:
        return None

    matches = []
    for r in records:
        if area_districts and r["district"].lower() not in area_districts:
            continue
        if area_provinces and r["province"].lower() not in area_provinces:
            continue
        tokens = set(re.findall(
            r"[a-z]+", (r["sub_category"] + " " + r["category"]).lower()))
        if all(t in tokens for t in type_words):
            matches.append(r)

    place = ", ".join(area_districts + [p.title() for p in area_provinces])
    kind = " ".join(type_words)
    if not matches:
        return (f"I found no {kind} entities in {place.title()} in the RDB list.",
                [])

    shown = matches[:LIST_LIMIT]
    heading = (
        f"There are {len(matches)} {kind} entities in {place.title()} in the "
        f"RDB list. "
        + (
            f"Showing the first {len(shown)}:"
            if len(matches) > len(shown)
            else "Results:"
        )
    )
    table = {
        "kind": "entity_list",
        "rows": [entity_table_row(record) for record in shown],
    }
    return heading, [r["entity_name"] for r in shown], table


# ---------- Fast path 2: questions about ONE business ----------
def exact_answer(scored, words):
    if not scored:
        return None
    top = scored[0]
    ties = [s for s in scored if s[0] == top[0] and s[1] == top[1]]
    if not (top[0] >= 0.99 and len(ties) == 1):
        return None
    intents = detect_intents(words)
    if not (intents or len(words) <= 4):
        return None
    record = records[top[2]]
    text = f"Details for {record['entity_name']}."
    return (
        text,
        [record["entity_name"]],
        entity_answer(record),
    )


# ---------- Fast path 3: "Did you mean ...?" for unclear names ----------
def candidates_answer(scored, words):
    if not scored or set(words) & LAW_WORDS:
        return None
    top = scored[0]
    if len(words) > 5 or top[0] < 0.5:
        return None
    if top[0] >= 0.99:
        candidates = [s for s in scored if s[0] == top[0] and s[1] == top[1]][:5]
    else:
        candidates = [s for s in scored if s[1] >= top[1]][:5]
    options = [
        f"{records[i]['entity_name']} ({records[i]['sub_category']}, "
        f"{records[i]['district']})" for _, _, i in candidates
    ]
    text = ("I found these possible matches: " + "; ".join(options)
            + ". Please type the full name of the one you mean.")
    return text, [records[i]["entity_name"] for _, _, i in candidates]


# =====================================================================
# Language model path (law questions)
# =====================================================================
SYSTEM_PROMPT = (
    "You are TourismGuard AI, an assistant about Rwanda's tourism law "
    "(Law No 12ter/2014) and licensed tourism entities. "
    "Answer ONLY using the context provided. "
    "Cite the sources you used in square brackets, like [Article 10] or "
    "[Musanze Cave Hotel]. "
    "If the context does not contain the answer, reply exactly: "
    "I could not find this in the documents. "
    "Keep the answer short and clear."
)


def answer(question):
    start = time.time()

    scored, words = find_entities(question)
    for fast in (list_answer(words), exact_answer(scored, words),
                 candidates_answer(scored, words)):
        if fast is not None:
            text, sources = fast[:2]
            result = {
                "answer": text,
                "sources": sources,
                "seconds": round(time.time() - start, 2),
            }
            if len(fast) == 3:
                result["entity_table"] = fast[2]
            return result

    results = retrieve(question)

    # Layer 1: score guard. A weak best match means the question is out of scope,
    # so we refuse without calling the language model at all.
    if results[0][1] < REFUSAL_THRESHOLD:
        return {
            "answer": REFUSAL_TEXT,
            "sources": [doc["ref"] for doc, _ in results],
            "seconds": round(time.time() - start, 2),
        }

    context = "\n".join(
        f"[{doc['ref']}] {doc['text'][:MAX_CONTEXT_CHARS]}"
        for doc, _ in results
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt")

    output = llm.generate(
        **inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=False,
    )
    new_tokens = output[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    # Layer 2 is the prompt above. Citations are added by the code, because the
    # small model does not reliably write them: cite the best-matching document,
    # plus any entity named in the answer.
    refusal_markers = ("could not find", "couldn't find", "sorry",
                       "can't assist", "cannot assist", "i cannot", "i can't")
    refused = any(marker in text.lower() for marker in refusal_markers)
    if refused:
        text = REFUSAL_TEXT
    cited = []
    if not refused:
        cited.append(results[0][0]["ref"])
        for doc, _ in results:
            if doc["source"] == "entity" and doc["ref"].lower() in text.lower():
                cited.append(doc["ref"])
        cited = list(dict.fromkeys(cited))   # remove duplicates, keep order
    if cited:
        text += "\n\nSources: " + ", ".join(f"[{c}]" for c in cited)

    return {
        "answer": text,
        "sources": [doc["ref"] for doc, _ in results],
        "seconds": round(time.time() - start, 2),
    }


if __name__ == "__main__":
    test_questions = [
        "What is the phone number of Kigali Serena Hotel?",
        "serena",
        "Which hotels are in Musanze?",
        "How many restaurants are in Gasabo?",
        "How long is an operating license valid?",
        "Who won the 2022 football World Cup?",
    ]

    for question in test_questions:
        result = answer(question)
        print()
        print("Question:", question)
        print("Answer  :", result["answer"])
        print("Time    :", result["seconds"], "seconds")