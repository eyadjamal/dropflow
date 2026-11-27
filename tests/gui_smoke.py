"""Native GUI workflow smoke test. On Linux run under xvfb-run or a desktop."""
from pathlib import Path
import importlib.machinery
import importlib.util
import hashlib
import os
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        os.environ['XDG_CONFIG_HOME'] = str(temporary/'config')
        os.environ['APPDATA'] = str(temporary/'config')
        loader = importlib.machinery.SourceFileLoader('dropflow_gui_smoke',str(ROOT/'DropFlow.pyw'))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        df = importlib.util.module_from_spec(spec)
        sys.modules[loader.name] = df
        loader.exec_module(df)
        good, bad = temporary/'sample.pdf', temporary/'broken.pdf'
        with df.fitz.open() as doc:
            for index in range(3):
                page = doc.new_page()
                page.insert_text((72,72), f'DropFlow Linux page {index+1}', fontsize=24)
            doc.save(good)
        original = hashlib.sha256(good.read_bytes()).hexdigest()
        bad.write_text('invalid PDF')
        if df.IS_LINUX and os.environ.get('DROPFLOW_TEST_NO_DND'):
            def unavailable_dnd():
                raise RuntimeError('Simulated unavailable TkDND')
            df.TkinterDnD.Tk = unavailable_dnd
        app = df.App()
        # Windows CI/sandbox desktops can deny tray message-filter access.
        # Exercise Tk workflows without starting that separate shell surface.
        if df.IS_WINDOWS:
            app.icon = None
        app.cfg['check_updates'] = False
        if os.environ.get('DROPFLOW_TEST_THEME'):
            app.apply_appearance(os.environ['DROPFLOW_TEST_THEME'], reduce_motion=True)
        errors, complete = [], []
        app.root.report_callback_exception = lambda *args: errors.append(str(args))
        def wait(predicate, seconds=30):
            deadline = time.monotonic()+seconds
            while not predicate() and time.monotonic()<deadline:
                app.root.update()
                time.sleep(.03)
            if not predicate():
                raise AssertionError('Timed out waiting for UI workflow')
        def scenario():
            try:
                workspace = app.open_workspace()
                assert workspace.winfo_exists()
                from tkinter import ttk
                assert ttk.Style(app.root).lookup('TFrame', 'background') == df.BG
                app.cfg['reduce_motion'] = True
                screenshot = os.environ.get('DROPFLOW_WORKSPACE_SCREENSHOT')
                if screenshot:
                    from PIL import ImageGrab
                    app.root.update()
                    x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
                    (ImageGrab.grab(window=app.root.winfo_id()) if df.IS_WINDOWS else ImageGrab.grab(bbox=(x,y,x+app.root.winfo_width(),y+app.root.winfo_height()))).save(screenshot)
                app.show_paths([str(good),str(bad)])
                win = app.win
                win._search_var.set('shrink pdf')
                wait(lambda: win._search_job is None and len(win._action_buttons) == 1)
                assert len(win._action_buttons) == 1
                win._first_action()
                assert win.state == 'params'
                win.show_menu([good,bad])
                menu_shot = os.environ.get('DROPFLOW_MENU_SCREENSHOT')
                if menu_shot:
                    wait(lambda: len(win._thumb_refs) >= 1 or not win._preview_tick)
                    from PIL import ImageGrab
                    app.root.update()
                    x,y=win.top.winfo_rootx(),win.top.winfo_rooty()
                    (ImageGrab.grab(window=win.top.winfo_id()) if df.IS_WINDOWS else ImageGrab.grab(bbox=(x,y,x+win.top.winfo_width(),y+win.top.winfo_height()))).save(menu_shot)
                action = next(a for a in win.actions if a.label=='Export pages as PNG')
                win.start(action,{'dpi':72})
                panel = win._output_panel
                panel.folder.set(str(temporary/'outputs'))
                panel.pattern.set('{name}_linux')
                panel.name.set('Linux export')
                panel.save()
                panel.submit()
                wait(lambda:not win.busy)
                assert {i.source.name:i.status for i in win._batch_items} == {'sample.pdf':'Done','broken.pdf':'Failed'}
                good_item = next(i for i in win._batch_items if i.source==good)
                saved = good_item.outputs[:]
                assert saved[0].parent == temporary/'outputs'
                bad.write_bytes(good.read_bytes())
                win.start(action, win._batch_options, retry=True)
                wait(lambda:not win.busy)
                assert all(i.status=='Done' for i in win._batch_items)
                assert good_item.outputs==saved
                assert len(app.cfg['recent_activity']) == 2
                workspace.refresh()
                assert len(workspace.records) == 2
                filled = os.environ.get('DROPFLOW_WORKSPACE_FILLED_SCREENSHOT')
                if filled:
                    from PIL import ImageGrab
                    app.root.update()
                    x,y=app.root.winfo_rootx(),app.root.winfo_rooty()
                    (ImageGrab.grab(window=app.root.winfo_id()) if df.IS_WINDOWS else ImageGrab.grab(bbox=(x,y,x+app.root.winfo_width(),y+app.root.winfo_height()))).save(filled)
                workspace.use_inputs()
                assert win.state == 'menu'
                history_count = len(app.cfg['recent_activity'])
                app.cfg['remember_recent'] = False
                win.show_menu([good,bad])
                organizer_action = next(a for a in win.actions if a.func==df.act_organize_pdf)
                win.choose(organizer_action)
                organizer = win._organizer
                selected = organizer.model.pages[-1].uid
                organizer.model.move(selected,0)
                organizer.selected = selected
                organizer.rotate(90)
                wait(lambda:len(organizer.images)==6 and hasattr(organizer,'preview_image'))
                preview_path = os.environ.get('DROPFLOW_SMOKE_SCREENSHOT')
                if preview_path:
                    from PIL import ImageGrab
                    app.root.update()
                    x,y=organizer.winfo_rootx(),organizer.winfo_rooty()
                    (ImageGrab.grab(window=organizer.winfo_id()) if df.IS_WINDOWS else ImageGrab.grab(bbox=(x,y,x+organizer.winfo_width(),y+organizer.winfo_height()))).save(preview_path)
                organizer.save()
                win._output_panel.folder.set(str(temporary/'organized'))
                win._output_panel.submit()
                wait(lambda:not win.busy)
                assert all(i.status=='Done' for i in win._batch_items)
                with df.fitz.open(win._batch_items[0].outputs[0]) as doc:
                    assert len(doc)==6 and doc[0].rotation==90
                assert hashlib.sha256(good.read_bytes()).hexdigest()==original
                assert len(app.cfg['recent_activity']) == history_count
                app.cfg['remember_recent'] = True
                df.set_language('ar')
                win.show_menu([good])
                win.show_output_options(action,{'dpi':72})
                app.root.update()
                app._open_settings()
                app.root.update()
                assert app.settings.alive
                assert not errors, errors
                complete.append(True)
                print('PASS native GUI: workspace, intent search, keyboard action, history/privacy, previews, presets, retry, PDF organizer, settings, Arabic',flush=True)
            except Exception:
                import traceback
                traceback.print_exc()
            finally:
                app.quit()
        app.root.after(200, scenario)
        app.run()
        return 0 if complete else 1

if __name__=='__main__':
    raise SystemExit(main())

