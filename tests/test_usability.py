import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recent_activity import remember, clean_history, existing_inputs, LIMIT
from action_menu import search_actions, sections
from preview_loader import PreviewLoader, render_preview
from batch_jobs import ItemResult

class UsabilityTests(unittest.TestCase):
    def test_search_intent_and_multiple_tokens(self):
        def act_compress_pdfs(): pass
        def act_merge_pdfs(): pass
        compress = SimpleNamespace(func=act_compress_pdfs, label="Compress PDFs")
        merge = SimpleNamespace(func=act_merge_pdfs, label="Merge PDFs")
        self.assertEqual(search_actions([merge, compress], "shrink pdf"), [compress])
        self.assertEqual(search_actions([merge, compress], "combine"), [merge])
        self.assertEqual(search_actions([merge, compress], "تصغير"), [compress])
        self.assertEqual(search_actions([merge, compress], "unrelated"), [])
        self.assertEqual(sections([merge, compress], [], {})[1][0], "Suggested")

    def test_history_is_bounded_and_preserves_failures(self):
        items = [ItemResult(Path('a.pdf'), status='Done', outputs=[Path('a.png')]),
                 ItemResult(Path('b.pdf'), status='Failed', error='private document contents')]
        history = []
        for index in range(20):
            history = remember(history, "Export", items)
        self.assertEqual(len(history), LIMIT)
        self.assertEqual(history[0]['outputs'], ['a.png'])
        self.assertIn('1 failed', history[0]['status'])
        self.assertNotIn('private document contents', str(history))
        self.assertEqual(clean_history(None), [])
        self.assertEqual(clean_history([{}, 'bad']), [])

    def test_large_history_never_reuses_partial_input_selection(self):
        items = [ItemResult(Path(f'{n}.pdf')) for n in range(205)]
        record = remember([], 'Merge', items)[0]
        self.assertFalse(record['complete_inputs'])
        self.assertEqual(existing_inputs(record)[0], [])

    def test_history_missing_input_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder)/'input.txt'
            file.write_text('sample')
            record = {'sources': [str(file), str(file.with_name('missing.txt'))]}
            self.assertEqual(existing_inputs(record), ([file], 1))

    def test_preview_worker_renders_and_handles_bad_files(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder)/'image.png'
            Image.new('RGB', (300,100)).save(file)
            loader = PreviewLoader()
            try:
                loader.request(1, file)
                token, path, image = loader.results.get(timeout=8)
                self.assertEqual(token, 1)
                self.assertEqual(path, file)
                self.assertEqual(image.size, (44,15))
                file.write_text('invalid image')
                loader.request(2, file)
                self.assertIsNone(loader.results.get(timeout=8)[2])
            finally:
                loader.close()

    def test_pdf_preview_is_bounded(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder)/'sample.pdf'
            with pymupdf.open() as document:
                document.new_page(width=1000, height=2000)
                document.save(file)
            preview = render_preview(file)
            self.assertLessEqual(max(preview.size), 44)
