import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint
from grazi import Controller, Settings, STYLE
from speech import Speech, speech_chunks

APP = QApplication.instance() or QApplication([])
APP.setStyleSheet(STYLE)


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, GRAZI_DATA_DIR=self.directory.name)
        self.env.start()
        self.c = Controller(APP)
        self.c.show_balloon()
        APP.processEvents()

    def tearDown(self):
        self.c.stop_voice()
        APP.removeEventFilter(self.c.activity_filter)
        self.c.activity_filter.deleteLater()
        self.c.pet.timer.stop()
        for widget in [self.c.window, self.c.pet, self.c.balloon]:
            widget.close(); widget.deleteLater()
        self.c.tray.hide()
        self.c.speech.deleteLater()
        self.env.stop(); self.directory.cleanup()

    def test_startup_compact_and_popup_optional(self):
        self.assertTrue(self.c.balloon.isVisible())
        self.assertFalse(self.c.window.isVisible())
        self.assertEqual(len(self.c.pet.frames), 4)
        self.assertTrue(all(not p.isNull() for p in self.c.pet.frames))
        self.c.show_chat()
        self.assertTrue(self.c.window.isVisible())

    def test_balloon_touch_targets_and_accessible_names(self):
        self.assertEqual((self.c.balloon.width(), self.c.balloon.height()), (336, 232))
        self.assertGreaterEqual(self.c.balloon.prev_button.width(), 32)
        self.assertGreaterEqual(self.c.balloon.next_button.width(), 32)
        self.assertGreaterEqual(self.c.balloon.send_button.width(), 36)
        self.assertEqual(self.c.balloon.prev_button.accessibleName(), 'Resposta anterior')
        self.assertEqual(self.c.balloon.next_button.accessibleName(), 'Próxima resposta')
        self.assertEqual(self.c.balloon.send_button.accessibleName(), 'Enviar mensagem')
        self.assertEqual(self.c.balloon.input.accessibleName(), 'Mensagem para a Grazi')
        self.assertFalse(self.c.balloon.prev_button.isEnabled())
        self.assertFalse(self.c.balloon.next_button.isEnabled())

    def test_settings_show_size_value_and_accessible_fields(self):
        dialog = Settings(self.c)
        try:
            self.assertEqual(dialog.size_value.text(), f"{self.c.state['size']} px")
            dialog.size.setValue(240); APP.processEvents()
            self.assertEqual(dialog.size_value.text(), '240 px')
            self.assertEqual(dialog.model.accessibleName(), 'Modelo local')
            self.assertEqual(dialog.file_root.accessibleName(), 'Pasta de trabalho')
            self.assertEqual(dialog.memory.accessibleName(), 'Memória editável')
        finally:
            dialog.close(); dialog.deleteLater()

    def test_balloon_send_and_history(self):
        self.c.balloon.input.setText('que horas são')
        self.c.balloon.send()
        self.assertIn('Agora são', self.c.balloon.label.text())
        self.assertEqual(self.c.state['history'][-2]['content'], 'que horas são')
        self.assertFalse(self.c.busy)
        self.assertFalse(self.c.window.isVisible())

    def test_error_restores_message(self):
        self.c.pending = {'role': 'user', 'content': 'mensagem a repetir'}
        self.c.busy = True
        self.c.on_answer('Falha simulada', False)
        self.assertEqual(self.c.balloon.input.text(), 'mensagem a repetir')
        self.assertTrue(self.c.balloon.send_button.isEnabled())
        self.assertEqual(self.c.state['history'], [])

    def test_anchor_screen_edges_and_drag(self):
        for point in [QPoint(0, 0), QPoint(500, 450)]:
            self.c.pet.move(point); APP.processEvents()
            self.c.balloon.reanchor()
            bounds = APP.primaryScreen().availableGeometry()
            self.assertTrue(bounds.contains(self.c.balloon.frameGeometry()))

    def test_pages_preserve_long_answer_and_follow_voice(self):
        text = 'Primeira frase. Segunda frase! ' + 'palavra ' * 90
        self.c.balloon.message(text)
        self.assertEqual(' '.join(self.c.balloon.pages).split(), text.split())
        self.c.speech.page.emit(1)
        self.assertEqual(self.c.balloon.label.text(), 'Segunda frase!')
        self.c.balloon.navigate(-1)
        self.assertEqual(self.c.balloon.index, 0)

    def test_cancel_rejects_late_audio_and_removes_file(self):
        speech = self.c.speech
        old = speech.token
        speech.stop()
        path = Path(self.directory.name) / 'late.mp3'
        path.write_bytes(b'late')
        speech._ready(old, str(path), '')
        self.assertFalse(path.exists())
        self.assertFalse(speech.active)

    def test_online_failure_restores_idle_with_visible_error(self):
        speech = self.c.speech
        speech.active = True
        speech._ready(speech.token, '', 'Falha simulada na voz online')
        self.assertFalse(speech.active)
        self.assertFalse(self.c.speaking)
        self.assertIn('Falha simulada', self.c.balloon.label.text())

    def test_opt_in_voice_persistence(self):
        self.assertEqual(self.c.state['voice_engine'], 'windows')
        self.c.state['voice_engine'] = 'edge'; self.c.persist()
        from core import load_state
        self.assertEqual(load_state()['voice_engine'], 'edge')

    def test_sleep_after_minute_and_wake_on_input(self):
        self.c.idle.last_activity -= 61
        self.c.pet.tick()
        self.assertTrue(self.c.idle.sleeping)
        self.assertFalse(self.c.balloon.isVisible())
        self.assertGreater(self.c.pet.sleep_blend, 0)
        self.assertFalse(self.c.pet.sleep_pix.isNull())
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent, Qt
        APP.sendEvent(self.c.balloon.input, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, 'a'))
        self.assertFalse(self.c.idle.sleeping)

    def test_no_sleep_while_waiting_for_speech_or_answer(self):
        for attribute in ['busy', 'listening', 'connecting']:
            self.c.idle.last_activity -= 61
            setattr(self.c, attribute, True); self.c.pet.tick()
            self.assertFalse(self.c.idle.sleeping)
            setattr(self.c, attribute, False)
        self.c.idle.last_activity -= 61
        self.c.speech.active = True; self.c.pet.tick()
        self.assertFalse(self.c.idle.sleeping)
        self.c.speech.active = False

    def test_idle_exact_boundary_and_reset(self):
        from idle import IdleState
        now = [0]
        idle = IdleState(clock=lambda: now[0])
        now[0] = 60; self.assertFalse(idle.update())
        now[0] = 60.01; self.assertTrue(idle.update())
        idle.touch(); self.assertFalse(idle.sleeping)
        now[0] = 100; self.assertFalse(idle.update())

    def test_chunk_bounds_and_plain_text(self):
        chunks = speech_chunks('a'*700)
        self.assertTrue(all(len(c) <= 180 for c in chunks))
        self.assertEqual(''.join(chunks), 'a'*700)
        self.c.balloon.message('<b>texto</b>')
        self.assertEqual(self.c.balloon.label.text(), '<b>texto</b>')

if __name__ == '__main__':
    unittest.main()
