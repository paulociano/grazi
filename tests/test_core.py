import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core


class Handler(BaseHTTPRequestHandler):
    body = None
    def log_message(self, *args): pass
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(json.dumps({"models": [{"name": "qwen3:1.7b"}, {"name": "large:cloud"}]}).encode())
    def do_POST(self):
        Handler.body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(200); self.end_headers()
        self.wfile.write(json.dumps({"message": {"content": "Oi, Paulo!"}}).encode())


class CoreTests(unittest.TestCase):
    def test_allowlisted_local_commands(self):
        self.assertRegex(core.local_command("que horas são"), r"Agora são \d{2}:\d{2}")
        self.assertEqual(core.local_command("calcule 12 * 8"), "O resultado é 96.")
        self.assertIsNone(core.local_command("abra terminal && del tudo"))
        self.assertIn("Não consegui", core.local_command("calcule 1 / 0"))
    def test_state_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            old = os.environ.get("GRAZI_DATA_DIR")
            os.environ["GRAZI_DATA_DIR"] = directory
            try:
                state = core.load_state(); state["memory"] = "Café e manhãs."
                core.save_state(state)
                self.assertEqual(core.load_state()["memory"], "Café e manhãs.")
                (Path(directory)/"state.json").write_text('{broken')
                self.assertEqual(core.load_state()["model"], "qwen3:1.7b")
                (Path(directory)/"state.json").write_text('{"history": [null, {"role":"system", "content":"bad"}], "size":9999}')
                self.assertEqual(core.load_state()["history"], [])
                self.assertEqual(core.load_state()["size"], 220)
                (Path(directory)/"state.json").write_text('{"wake_word": false}')
                self.assertTrue(core.load_state()["wake_word"])
                (Path(directory)/"state.json").write_text('{"wake_word": false, "wake_word_configured": true}')
                self.assertFalse(core.load_state()["wake_word"])
            finally:
                if old is None: os.environ.pop("GRAZI_DATA_DIR", None)
                else: os.environ["GRAZI_DATA_DIR"] = old

    def test_http_contract_and_local_filter(self):
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        old = core.OLLAMA; core.OLLAMA = f"http://127.0.0.1:{server.server_port}"
        try:
            self.assertEqual(core.list_models(), ["qwen3:1.7b"])
            answer = core.chat("qwen3:1.7b", "Paulo", [{"role": "user", "content": "Oi"}])
            self.assertEqual(answer, "Oi, Paulo!")
            self.assertEqual(Handler.body["options"]["num_ctx"], 2048)
            self.assertFalse(Handler.body["think"])
            self.assertEqual(Handler.body["messages"][-1]["content"], "Oi")
            with self.assertRaises(RuntimeError): core.chat("qwen:cloud", "", [])
        finally:
            core.OLLAMA = old; server.shutdown(); server.server_close(); thread.join()

    def test_unreachable_service_message(self):
        from unittest.mock import patch
        import urllib.error
        with patch("urllib.request.OpenerDirector.open", side_effect=urllib.error.URLError("refused")):
            with self.assertRaisesRegex(RuntimeError, "Abra o Ollama"):
                core.list_models()


if __name__ == "__main__": unittest.main()
