import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assistance import AssistantActions


class AssistanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.confirmed = []
        self.opened = []
        self.actions = AssistantActions(
            {"file_root": str(self.root)},
            lambda title, description: self.confirmed.append((title, description)) or True,
            opener=lambda path: self.opened.append(Path(path)),
            recycler=lambda path: Path(path).rename(self.root / (Path(path).name + ".recycled")),
        )

    def tearDown(self):
        self.directory.cleanup()

    def test_list_open_and_read_are_scoped_to_workspace(self):
        (self.root / "notas.txt").write_text("Olá, Grazi!", encoding="utf-8")
        self.assertIn("Arquivo: notas.txt", self.actions.execute("listar arquivos"))
        self.assertIn("Olá, Grazi!", self.actions.execute("ler arquivo notas.txt"))
        self.actions.execute("abrir arquivo notas.txt")
        self.assertEqual(self.opened, [self.root / "notas.txt"])
        with self.assertRaises(ValueError):
            self.actions.execute("ler arquivo ../fora.txt")

    def test_save_uses_utf8_and_confirmation_for_overwrite(self):
        self.assertIn("Salvei", self.actions.execute("salvar arquivo diario.md | primeira linha"))
        self.assertEqual((self.root / "diario.md").read_text(encoding="utf-8"), "primeira linha")
        self.actions.execute("salvar arquivo diario.md | segunda linha")
        self.assertEqual((self.root / "diario.md").read_text(encoding="utf-8"), "segunda linha")
        self.assertEqual(self.confirmed[0][0], "Substituir arquivo?")

    def test_delete_goes_to_recycle_callback_and_requires_confirmation(self):
        target = self.root / "apagar.txt"
        target.write_text("temporário", encoding="utf-8")
        result = self.actions.execute("excluir arquivo apagar.txt")
        self.assertIn("Lixeira", result)
        self.assertFalse(target.exists())
        self.assertTrue((self.root / "apagar.txt.recycled").exists())
        self.assertEqual(self.confirmed[0][0], "Mover para a Lixeira?")

    def test_save_last_answer(self):
        self.assertIn("Salvei", self.actions.execute("salvar resposta em resposta.txt", "Resposta da Grazi"))
        self.assertEqual((self.root / "resposta.txt").read_text(encoding="utf-8"), "Resposta da Grazi")

    def test_unsupported_and_unknown_commands_do_not_execute(self):
        (self.root / "programa.exe").write_bytes(b"MZ")
        with self.assertRaises(ValueError):
            self.actions.execute("abrir arquivo programa.exe")
        self.assertIsNone(self.actions.execute("execute qualquer comando perigoso"))


if __name__ == "__main__":
    unittest.main()
