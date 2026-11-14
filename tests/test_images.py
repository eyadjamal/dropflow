"""Supported image conversions and removed HEIC/HEIF entry points."""
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_core import df

class ImageTests(unittest.TestCase):
    def test_removed_formats_are_not_image_inputs(self):
        self.assertFalse({'.heic', '.heif', '.heics', '.heifs', '.hif'} & df.IMG_EXTS)
        self.assertNotIn('pillow_heif', df.__dict__)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'photo.heic'
            source.write_bytes(b'unsupported')
            _, actions = df.build_actions([source])
            self.assertFalse(any('Convert' in action.label or 'OCR' in action.label for action in actions))
            with self.assertRaisesRegex(ValueError, 'not supported'):
                df.load_image(source)

    def test_removed_targets_cannot_be_requested(self):
        for target in ('HEIC', 'HEIF'):
            with self.assertRaisesRegex(ValueError, 'Unsupported image target'):
                df.make_convert(target)

    def test_supported_image_conversions_and_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'photo.png'
            Image.new('RGB',(40,30),'blue').save(source)
            _, actions=df.build_actions([source])
            self.assertFalse(any('HEIC' in a.label or 'HEIF' in a.label for a in actions))
            for target in ('JPG','WEBP'):
                result=df.make_convert(target)([source],{},df.JobContext(lambda m:None))
                self.assertEqual(result.failed,0)
                with Image.open(result.outputs[0]) as converted:
                    self.assertEqual(converted.size,(40,30))

    def test_no_overwrite_naming(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'photo.jpg'
            first=df.derive_output(source,'.png')
            first.write_bytes(b'keep')
            self.assertEqual(df.derive_output(source,'.png').name,'photo_dropflow (1).png')
