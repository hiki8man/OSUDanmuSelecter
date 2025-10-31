import asyncio
import time
# AI写的（
class AsyncIRCClient:
    def __init__(self, host: str, port: int, nick: str, realname: str = None, password: str = None, reconnect_delay: int = 5):
        self.host = host
        self.port = port
        self.nick = nick
        self.realname = realname or nick
        self.password = password
        self.reconnect_delay = reconnect_delay
        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
        self.running = True

    async def _send_raw(self, message: str):
        if self.writer is None:
            return
        self.writer.write(f"{message}\r\n".encode())
        await self.writer.drain()

    async def connect(self):
        """连接到 IRC 服务器"""
        while self.running:
            try:
                print(f"[INFO] Connecting to {self.host}:{self.port} ...")
                self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

                if self.password:
                    await self._send_raw(f"PASS {self.password}")

                await self._send_raw(f"NICK {self.nick}")
                await self._send_raw(f"USER {self.nick} 0 * :{self.realname}")

                print("[INFO] Connected successfully.")
                await self.listen_forever()  # 进入主循环

            except Exception as e:
                print(f"[WARN] Connection lost: {e}")
                await asyncio.sleep(self.reconnect_delay)
                print("[INFO] Reconnecting...")

    async def listen_forever(self):
        """接收消息并保持心跳"""
        while self.running and not self.reader.at_eof():
            try:
                line = await self.reader.readline()
                if not line:
                    break
                message = line.decode(errors='ignore').strip()

                if message.startswith("PING"):
                    token = message.split()[1]
                    await self._send_raw(f"PONG {token}")
                    print(f"[PING] {message} -> PONG {token}")

            except Exception as e:
                print(f"[ERROR] Read loop failed: {e}")
                break

        print("[INFO] Listen loop exited.")

    async def send_privmsg(self, target: str, message: str):
        """向指定目标发送消息"""
        await self._send_raw(f"PRIVMSG {target} :{message}")

    async def close(self):
        self.running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        print("[INFO] Connection closed.")


