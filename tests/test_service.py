import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from organizer.service import FileOrganizer
from organizer import state

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.base=Path(self.temp.name); self.work=self.base/'work'; self.work.mkdir(); self.a=self.work/'a.txt'; self.a.write_text('same')
        self.patch=patch.object(state,'STATE_FILE',self.base/'ops.json'); self.patch.start(); self.s=FileOrganizer()
    def tearDown(self): self.patch.stop(); self.temp.cleanup()
    def test_scan_category(self): self.assertEqual(self.s.scan(self.work)[0]['category'],'Documents')
    def test_rename_undo(self):
        self.s.batch_rename(self.work,'{index:03d}_{name}'); self.assertTrue((self.work/'001_a.txt').exists()); self.s.undo_last(); self.assertTrue(self.a.exists())
    def test_duplicate_move_undo(self):
        b=self.work/'b.txt'; b.write_text('same'); groups=self.s.find_duplicates(self.work); self.assertEqual(len(groups),1); self.s.remove_duplicates(groups); self.s.undo_last(); self.assertTrue(b.exists())
if __name__=='__main__': unittest.main()
