import unittest
from pathlib import Path
from PIL import Image, ImageChops
from source_credit import score_credit, credit_cover


class SourceCreditTests(unittest.TestCase):
    def test_missing_author_stops_output(self):
        for source in [None, {}, {'author': 'unknown', 'basis': 'screenshot'}, {'author': 'sky荼苏'}]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                score_credit({'score_source': source})

    def test_source_author_is_distinct_from_performer(self):
        d = {'score_source': {'author': 'sky荼苏', 'basis': 'User confirmation'}, 'performer': 'Sunspark'}
        self.assertEqual(score_credit(d)['text'], 'by:sky荼苏')

    def test_small_corner_credit_keeps_the_other_image_pixels(self):
        source = Image.new('RGB', (1080, 1440), 'ivory')
        d = {'score_source': {'author': 'Example author', 'basis': 'Synthetic test'}}
        output = credit_cover(source, d, Path('.'))
        change = ImageChops.difference(source, output).getbbox()
        self.assertIsNotNone(change)
        self.assertGreater(change[0], 540)
        self.assertGreater(change[1], 1290)
        self.assertLessEqual(change[2], 1016)
        self.assertLessEqual(change[3], 1376)
        self.assertIsNone(ImageChops.difference(source.crop((0,0,1080,1200)), output.crop((0,0,1080,1200))).getbbox())

    def test_chinese_credit_requires_an_explicit_font(self):
        with self.assertRaisesRegex(ValueError, 'font_file'):
            credit_cover(Image.new('RGB', (1080,1080)), {'score_source': {'author':'sky荼苏','basis':'User'}}, Path('.'))


if __name__ == '__main__':
    unittest.main()
