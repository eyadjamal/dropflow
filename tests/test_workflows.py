import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pymupdf as fitz
from output_policy import output_scope, route_output, validate_pattern
from saved_presets import load_presets, save_preset
from pdf_organizer import read_pages, PageModel, export_pages

class Context:
    def check(self):
        pass
    def progress(self, text):
        pass

class WorkflowTests(unittest.TestCase):
    def test_output_routing_preserves_children_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base/'report.pdf'
            source.write_bytes(b'original')
            folder = base/'results'
            with output_scope([source], {'folder':str(folder), 'pattern':'{name}_{index}'}, 'split', 7):
                result = route_output(base/'report_split', True)
                self.assertEqual(result, folder/'report_7')
                result.mkdir()
                self.assertEqual(route_output(result/'page1.pdf'), result/'page1.pdf')
                output = route_output(base/'report.pdf')
                output.write_bytes(b'first')
                self.assertEqual(route_output(base/'report.pdf'), folder/'report_7 (1).pdf')
            self.assertEqual(route_output(base/'other.pdf'), base/'other.pdf')
            self.assertEqual(source.read_bytes(), b'original')

    def test_invalid_patterns_are_rejected(self):
        for pattern in ('../escape', '{unknown}', '{name!r}', '{index:04d}', 'CON', 'file.', '{name}/file'):
            with self.subTest(pattern=pattern), self.assertRaises(ValueError):
                validate_pattern(pattern)

    def test_output_scope_resets_after_error(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with self.assertRaises(RuntimeError):
                with output_scope([base/'a.pdf'], {'folder':str(base/'out')}, 'convert'):
                    raise RuntimeError('conversion failed')
            self.assertEqual(route_output(base/'a.pdf'), base/'a.pdf')

    def test_presets_upsert_and_do_not_capture_page_plans(self):
        options = {'quality':23, '_pdf_plan':[{'source':'private.pdf'}]}
        presets = save_preset([], 'video', 'Email', options, {'pattern':'{name}_small'})
        original_id = presets[0]['id']
        presets = save_preset(presets, 'video', 'email', {'quality':28}, {})
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]['id'], original_id)
        self.assertEqual(presets[0]['options'], {'quality':28})
        self.assertNotIn('_pdf_plan', load_presets(save_preset([], 'pdf', 'PDF', options, {}))[0]['options'])
        self.assertEqual(load_presets([{}, {'id':1}, None]), [])

    def test_pdf_order_rotation_delete_undo_and_originals(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            sources = []
            for index in range(2):
                path = base/f'input{index}.pdf'
                with fitz.open() as doc:
                    for number in range(2):
                        page = doc.new_page()
                        page.insert_text((72,72), f'Document {index} Page {number}')
                    doc[0].set_rotation(90)
                    doc.save(path)
                sources.append(path)
            hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in sources]
            model = PageModel(read_pages(sources))
            last = model.pages[-1]
            model.move(last.uid, 0)
            model.rotate(last.uid)
            removed = model.pages[1]
            model.remove(removed.uid)
            model.undo()
            self.assertEqual(len(model.pages),4)
            output = base/'organized.pdf'
            export_pages(model.plan(), output, sources, Context())
            with fitz.open(output) as doc:
                self.assertIn('Document 1 Page 1', doc[0].get_text())
                self.assertEqual(doc[0].rotation,90)
                self.assertEqual(doc[1].rotation,90)
            self.assertEqual(hashes,[hashlib.sha256(p.read_bytes()).hexdigest() for p in sources])

    def test_pdf_export_failure_cleans_temporary_and_protects_existing(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            source=base/'input.pdf'
            with fitz.open() as doc:
                doc.new_page()
                doc.save(source)
            plan=PageModel(read_pages([source])).plan()
            output=base/'existing.pdf'
            output.write_bytes(b'keep me')
            with self.assertRaises(FileExistsError):
                export_pages(plan,output,[source],Context())
            self.assertEqual(output.read_bytes(),b'keep me')
            self.assertEqual(list(base.glob('.dropflow-*')),[])
            plan[0]['source']=str(base/'unexpected.pdf')
            with self.assertRaises(ValueError):
                export_pages(plan,base/'new.pdf',[source],Context())
            self.assertFalse((base/'new.pdf').exists())

    def test_pdf_cancellation_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            source=base/'input.pdf'
            with fitz.open() as doc:
                doc.new_page()
                doc.save(source)
            def cancel():
                raise InterruptedError('cancelled')
            with self.assertRaises(InterruptedError):
                export_pages(PageModel(read_pages([source])).plan(),base/'output.pdf',[source],
                             SimpleNamespace(check=cancel,progress=lambda text:None))
            self.assertFalse((base/'output.pdf').exists())
            self.assertEqual(list(base.glob('.dropflow-*')),[])

    def test_real_split_image_and_archive_outputs_follow_policy(self):
        from test_core import df
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base/'input.pdf'
            with fitz.open() as document:
                document.new_page()
                document.new_page()
                document.save(source)
            folder = base/'results'
            settings = {'folder':str(folder), 'pattern':'{name}_ready'}
            context = df.JobContext(lambda text:None)
            with output_scope([source], settings, 'split'):
                result = df.act_split_pdf([source], {'pages':1}, context)
            self.assertEqual(result.failed, 0)
            self.assertEqual(Path(result.outputs[0]), folder/'input_ready')
            self.assertEqual(len(list((folder/'input_ready').glob('*.pdf'))),2)
            image = base/'photo.png'
            Image.new('RGB',(30,30),'red').save(image)
            with output_scope([image], settings, 'convert'):
                result = df.make_convert('JPG')([image], {}, context)
            self.assertEqual(Path(result.outputs[0]),folder/'photo_ready.jpg')
            with output_scope([image], settings, 'archive'):
                result = df.act_zip([image], {}, context)
            self.assertEqual(Path(result.outputs[0]),folder/'photo_ready.zip')
            self.assertTrue(source.exists() and image.exists())
