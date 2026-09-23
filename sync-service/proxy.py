import socket
import threading
import time
import secrets
from collections import deque

class VolatileSyncService:
    def __init__(self, local_port=18888, core_port=19999, chunk_size=512):
        self.local_port = local_port
        self.core_port = core_port
        self.chunk_size = chunk_size
        self.running = True
        self.stream_queue = deque()
        
    def start_service(self):
        self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.proxy_socket.bind(('127.0.0.1', self.local_port))
        self.proxy_socket.listen(5)
        
        threading.Thread(target=self._obfuscated_traffic_pump, daemon=True).start()
        threading.Thread(target=self._listen_to_ui, daemon=True).start()

    def _listen_to_ui(self):
        while self.running:
            try:
                ui_conn, _ = self.proxy_socket.accept()
                threading.Thread(target=self._handle_ui_stream, args=(ui_conn,), daemon=True).start()
            except Exception:
                break

    def _handle_ui_stream(self, ui_conn):
        buffer = bytearray()
        try:
            while self.running:
                data = ui_conn.recv(self.chunk_size)
                if not data:
                    break
                buffer.extend(data)
                
                while len(buffer) >= self.chunk_size:
                    chunk = buffer[:self.chunk_size]
                    del buffer[:self.chunk_size]
                    self.stream_queue.append(bytes(chunk))
        except Exception:
            pass
        finally:
            ui_conn.close()
            self._secure_wipe_bytearray(buffer)

    def _obfuscated_traffic_pump(self):
        while self.running:
            try:
                core_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                core_sock.connect(('127.0.0.1', self.core_port))
                
                while self.running:
                    if self.stream_queue:
                        real_data = self.stream_queue.popleft()
                        core_sock.sendall(real_data)
                    else:
                        decoy_packet = b'\x00' + secrets.token_bytes(self.chunk_size - 1)
                        core_sock.sendall(decoy_packet)
                        
                    time.sleep(0.05) 
            except Exception:
                time.sleep(1) 

    def _secure_wipe_bytearray(self, ba):
        if ba:
            for i in range(len(ba)):
                ba[i] = 0

    def terminate(self):
        self.running = False
        self.proxy_socket.close()
        while self.stream_queue:
            try:
                packet = self.stream_queue.popleft()
                del packet
            except IndexError:
                break
