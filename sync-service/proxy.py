import asyncio, secrets

class VolatileSyncService:
    def __init__(self, local_port=18888, core_port=19999, chunk_size=512):
        self.local_port = local_port
        self.core_port = core_port
        self.chunk_size = chunk_size
        self.running = True
        
        self.q = asyncio.Queue(maxsize=1000)

    def start_service(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._server_init())
        loop.create_task(self._pump())

    async def _server_init(self):
        server = await asyncio.start_server(self._handle_ui, '127.0.0.1', self.local_port)
        async with server: await server.serve_forever()

    async def _handle_ui(self, reader, writer):
        buf = bytearray()
        try:
            while self.running:
                data = await reader.read(self.chunk_size)
                if not data: break
                buf.extend(data)
                
                while len(buf) >= self.chunk_size:
                    try: await asyncio.wait_for(self.q.put(bytes(buf[:self.chunk_size])), timeout=0.5)
                    except asyncio.TimeoutError: pass
                    del buf[:self.chunk_size]
        except: pass
        finally:
            writer.close()
            await writer.wait_closed()
            if buf:
                for i in range(len(buf)): buf[i] = 0

    async def _pump(self):
        while self.running:
            try:
                reader, writer = await asyncio.open_connection('127.0.0.1', self.core_port)
                
                while self.running:
                    try:
                        real_data = await asyncio.wait_for(self.q.get(), timeout=0.02)
                        writer.write(real_data)
                        await writer.drain()
                        self.q.task_done()
                    except asyncio.TimeoutError:
                        writer.write(secrets.token_bytes(self.chunk_size))
                        await writer.drain()
                    
                    await asyncio.sleep(0.01) 
            except:
                await asyncio.sleep(2) 

    def terminate(self):
        self.running = False
