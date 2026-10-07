import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class FakeEmbedder:
    def encode(self, *args, **kwargs):
        raise AssertionError("The mocked tests should not encode questions.")


class FakeTokenizer:
    def apply_chat_template(self, *args, **kwargs):
        return "test prompt"

    def __call__(self, *args, **kwargs):
        return {"input_ids": torch.tensor([[1, 2, 3]])}

    def decode(self, *args, **kwargs):
        return "The Board may temporarily suspend an operating licence."


class FakeLanguageModel:
    def __init__(self):
        self.generate_calls = []

    def eval(self):
        return self

    def generate(self, **kwargs):
        self.generate_calls.append(kwargs)
        return torch.tensor([[1, 2, 3, 4]])


fake_language_model = FakeLanguageModel()
with (
    patch("sentence_transformers.SentenceTransformer", return_value=FakeEmbedder()),
    patch.object(AutoTokenizer, "from_pretrained", return_value=FakeTokenizer()),
    patch.object(
        AutoModelForCausalLM, "from_pretrained", return_value=fake_language_model
    ),
):
    import rag


class RagAnswerTests(unittest.TestCase):
    def setUp(self):
        fake_language_model.generate_calls.clear()

    def test_exact_entity_question_uses_local_entity_data(self):
        result = rag.answer("Where is GORILLA HUB SAFARIS LTD located?")

        table = result["entity_table"]
        self.assertEqual(table["kind"], "entity")
        self.assertEqual(table["name"], "GORILLA HUB SAFARIS LTD")
        details = dict(table["details"])
        self.assertEqual(details["District"], "Nyarugenge")
        self.assertEqual(details["Phone"], "0795868827")
        self.assertEqual(details["Email"], "reservations@gorillahubsafaris.com")
        self.assertNotIn("Description", details)
        self.assertEqual(
            table["links"],
            [
                {
                    "label": "Open business website",
                    "url": "https://gorillahubsafaris.com/",
                },
                {
                    "label": "Open official RDB profile",
                    "url": "https://tourismregulation.rw/en/entity/profile/2170/",
                },
            ],
        )
        self.assertEqual(fake_language_model.generate_calls, [])

    def test_district_list_question_uses_local_entity_data(self):
        result = rag.answer("Which hotels are in Musanze?")

        table = result["entity_table"]
        self.assertIn("hotel entities in Musanze", result["answer"])
        self.assertEqual(table["kind"], "entity_list")
        home_inn = next(row for row in table["rows"] if row["Business"] == "HOME INN")
        self.assertEqual(home_inn["Phone"], "+25078834127")
        self.assertEqual(home_inn["Email"], "info@homeinnhotel.com")
        self.assertEqual(home_inn["Website"], "https://www.homeinnhotel.com")
        self.assertEqual(
            home_inn["RDB profile"],
            "https://tourismregulation.rw/en/entity/profile/287/",
        )
        self.assertNotIn("Description", home_inn)
        self.assertEqual(fake_language_model.generate_calls, [])

    def test_law_answer_uses_retrieved_context_and_cites_source(self):
        document = {
            "ref": "Article 10",
            "text": "The Board may temporarily suspend an operating licence.",
            "source": "law",
        }
        with (
            patch.object(rag, "find_entities", return_value=([], ["licence"])),
            patch.object(rag, "retrieve", return_value=[(document, 0.9)]),
        ):
            result = rag.answer("Who may suspend a licence?")

        self.assertIn("Article 10", result["answer"])
        self.assertEqual(result["sources"], ["Article 10"])
        self.assertEqual(len(fake_language_model.generate_calls), 1)
        self.assertFalse(fake_language_model.generate_calls[0]["do_sample"])

    def test_weak_retrieval_score_refuses_without_generating(self):
        document = {
            "ref": "Article 10",
            "text": "Tourism licence provisions.",
            "source": "law",
        }
        with (
            patch.object(rag, "find_entities", return_value=([], ["weather"])),
            patch.object(rag, "retrieve", return_value=[(document, 0.1)]),
        ):
            result = rag.answer("What is tomorrow's weather?")

        self.assertEqual(
            result["answer"], "I could not find this in the documents."
        )
        self.assertEqual(fake_language_model.generate_calls, [])


if __name__ == "__main__":
    unittest.main()
