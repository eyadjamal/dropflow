"""Single-instance IPC and Explorer command tests."""
import json
import queue
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import importlib.machinery
import importlib.util

loader = importlib.machinery.SourceFileLoader("dropflow_ipc", str(ROOT / "DropFlow.pyw"))
spec = importlib.util.spec_from_file_location("dropflow_ipc",
                                              str(ROOT / "DropFlow.pyw"), loader=loader)
df = importlib.util.module_from_spec(spec)
sys.modules["dropflow_ipc"] = df
spec.loader.exec_module(df)


class IPCTests(unittest.TestCase):
    def test_send_to_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            instance = Path(tmp) / "instance.json"
            received = []

            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            instance.write_text(json.dumps({"port": port}), encoding="utf-8")

            def receive():
                conn, _ = server.accept()
                with conn:
                    received.append(conn.recv(4096))
                    conn.sendall(b"OK\n")
                server.close()

            thread = threading.Thread(target=receive, daemon=True)
            thread.start()
            with mock.patch.object(df, "INSTANCE_PATH", instance):
                sent = df._send_to_existing([str(Path(tmp) / "file.txt")])
            thread.join(2)
            self.assertTrue(sent)
            self.assertTrue(received and b"file.txt" in received[0])

    def test_cli_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a b.txt"
            path.write_text("x", encoding="utf-8")
            with mock.patch.object(sys, "argv", ["DropFlow.pyw", "--send", str(path)]):
                paths = df._cli_paths()
            self.assertEqual(paths, [str(path.resolve())])

    def test_explorer_command(self):
        command = df.explorer_command()
        self.assertIn("--send", command)
        self.assertIn("%1", command)

    def test_ipc_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            instance = data_dir / "instance.json"
            app = object.__new__(df.App)
            app.q = queue.Queue()
            app._ipc_sock = None
            app._ipc_stop = threading.Event()
            app._ipc_thread = None
            with mock.patch.object(df, "DATA_DIR", data_dir), \
                    mock.patch.object(df, "INSTANCE_PATH", instance):
                app._start_ipc()
                try:
                    info = json.loads(instance.read_text(encoding="utf-8"))
                    with socket.create_connection(("127.0.0.1", info["port"]),
                                                  timeout=2) as sock:
                        sock.sendall(b'{"paths": ["C:/x.txt"]}\n')
                        self.assertEqual(sock.recv(3), b"OK\n")
                    message = app.q.get(timeout=2)
                    self.assertEqual(message[0], "incoming")
                    self.assertEqual(message[1]["paths"], ["C:/x.txt"])
                finally:
                    app._stop_ipc()


if __name__ == "__main__":
    unittest.main()
