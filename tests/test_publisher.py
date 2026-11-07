import importlib.util
from pathlib import Path
import unittest
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('publisher',root/'publisher.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class PublisherTest(unittest.TestCase):
    def test_queue_material(self):
        q=mod.queue()
        self.assertGreaterEqual(len(q['posts']),25)
        self.assertEqual(q['posts'][0]['type'],'REELS')
        self.assertTrue(all(x['approved'] for x in q['posts']))
        self.assertTrue(all('V6' not in x['title'] and 'V6' not in x['caption'] for x in q['posts']))
    def test_next_post(self):
        self.assertEqual(mod.next_post()['id'],'REEL01')
    def test_url_construction(self):
        import os
        before=os.environ.get('GITHUB_REPOSITORY')
        beforebase=os.environ.pop('MEDIA_BASE_URL',None)
        os.environ['GITHUB_REPOSITORY']='testuser/ig-auto'
        try: self.assertEqual(mod.media_base(),'https://testuser.github.io/ig-auto/media')
        finally:
            if before is None:os.environ.pop('GITHUB_REPOSITORY',None)
            else:os.environ['GITHUB_REPOSITORY']=before
            if beforebase is not None:os.environ['MEDIA_BASE_URL']=beforebase
if __name__=='__main__':unittest.main()
