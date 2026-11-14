import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from batch_jobs import ItemResult, execute, is_combined
from action_menu import identity, sections
from quality_presets import values

class Cancelled(Exception): pass
class Context:
    cancelled=False

class ReleaseTests(unittest.TestCase):
    def test_partial_failure_and_retry_preserves_success(self):
        calls=[]
        def convert(paths, opts, ctx):
            calls.append(paths[0].name)
            if paths[0].name=='bad.pdf' and len(calls)==2:
                return SimpleNamespace(failed=1,message='Failed',errors=['Password required'],outputs=[])
            return SimpleNamespace(failed=0,outputs=[paths[0].with_suffix('.out')],preview=None,clipboard=None)
        action=SimpleNamespace(func=convert)
        items=[ItemResult(Path('good.pdf')),ItemResult(Path('bad.pdf'))]
        execute(action,items,{},Context(),lambda item:None,Cancelled)
        self.assertEqual([i.status for i in items],['Done','Failed'])
        self.assertEqual(items[1].error,'Password required')
        first_output=items[0].outputs[:]
        execute(action,[i for i in items if i.status=='Failed'],{},Context(),lambda i:None,Cancelled)
        self.assertEqual(calls,['good.pdf','bad.pdf','bad.pdf'])
        self.assertEqual(items[0].outputs,first_output)
        self.assertEqual(items[1].status,'Done')

    def test_cancellation_does_not_run_pending(self):
        ctx=Context();ctx.cancelled=True
        def convert(*args): self.fail('cancelled batch ran a conversion')
        items=[ItemResult(Path('a')),ItemResult(Path('b'))]
        execute(SimpleNamespace(func=convert),items,{},ctx,lambda i:None,Cancelled)
        self.assertTrue(all(i.status=='Cancelled' for i in items))

    def test_combined_partial_failure_keeps_output_and_marks_job_failed(self):
        def act_merge_pdfs(paths,opts,ctx):
            self.assertEqual(len(paths),2)
            return SimpleNamespace(failed=1,message='Partial',errors=['bad input'],outputs=[Path('partial.pdf')])
        action=SimpleNamespace(func=act_merge_pdfs)
        self.assertTrue(is_combined(action))
        items=[ItemResult(Path('a')),ItemResult(Path('b'))]
        execute(action,items,{},Context(),lambda i:None,Cancelled)
        self.assertTrue(all(i.status=='Failed' for i in items))
        self.assertEqual(items[0].outputs,[Path('partial.pdf')])

    def test_menu_no_duplicates_and_usage_order(self):
        def make(fmt):
            def run(*args): return fmt
            return SimpleNamespace(func=run,label=fmt)
        actions=[make(x) for x in ['PNG','JPG','WEBP','GIF','PDF','TXT']]
        self.assertNotEqual(identity(actions[0]),identity(actions[1]))
        groups=sections(actions,[identity(actions[0])],{identity(actions[5]):9})
        flattened=[identity(a) for _,group in groups for a in group]
        self.assertEqual(len(flattened),len(set(flattened)))
        self.assertEqual(groups[1][1][0],actions[5])
        self.assertEqual(len(groups[1][1]),3)

    def test_presets_only_for_quality(self):
        self.assertIsNone(values('pages',1,50,1))
        self.assertEqual(values('quality',10,95,60),(39,60,95))
        self.assertEqual(values('dpi',72,300,150),(72,150,300))
