# c2dglab.py

import asyncio
import logging
import pydglab
from pydglab import model_v3
import data_fetcher
import tkinter as tk
from tkinter import scrolledtext
import threading

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(module)s [%(levelname)s]: %(message)s",
    level=logging.INFO
)

def map_strength(value):
    """
    将强度值映射到设备的有效范围（0 到 100 的整数）
    """
    if value < 0:
        return 0
    elif value > 200:
        return 200
    return int(value)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("DGLab Controller")
        
        # Create UI elements
        self.create_widgets()
        
        # Initialize variables
        self.dglab_instance = pydglab.dglab_v3()
        self.last = 0

    def create_widgets(self):
        # Create input fields for wave parameters
        self.param_frame = tk.Frame(self.root)
        self.param_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        for i, (label_text, default_value) in enumerate([
            ("Param 1:", "1"), ("Param 2:", "9"), ("Param 3:", "20"),
            ("Param 4:", "5"), ("Param 5:", "35"), ("Param 6:", "20"),
            ("Tank Hit:", "5"), ("Tank Die:", "100"), ("G Force:", "10")
        ]):
            tk.Label(self.param_frame, text=label_text).grid(row=0, column=i, sticky="nsew")
            entry = tk.Entry(self.param_frame, justify="center")
            entry.grid(row=1, column=i, sticky="nsew")
            entry.insert(0, default_value)
            setattr(self, f"param{i+1}" if i < 6 else ["tankhit", "tankdie", "g_force"][i-6], entry)

        for i in range(9):
            self.param_frame.columnconfigure(i, weight=1)

        self.start_button = tk.Button(self.root, text="Start", command=self.start)
        self.start_button.pack(pady=10)

        # Create log display
        self.log_display = scrolledtext.ScrolledText(self.root, height=10)
        self.log_display.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        self.log_display.insert(tk.END, message + "\n")
        self.log_display.see(tk.END)

    async def connect_to_device(self):
        retry_count = 0
        max_retries = 5
        retry_delay = 5

        while retry_count < max_retries:
            try:
                self.log("正在连接到 郊狼 3.0...")
                await self.dglab_instance.create()
                self.log("成功连接到 郊狼 3.0！")
                return True
            except Exception as e:
                retry_count += 1
                self.log(f"连接失败（尝试 {retry_count}/{max_retries}）：{e}")
                if retry_count < max_retries:
                    self.log(f"{retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                else:
                    self.log("已达到最大重试次数，连接失败。")
                    return False

    async def connect_and_set_strength(self):
        if not await self.connect_to_device():
            return

        try:
            await self.dglab_instance.set_wave_sync(
                int(self.param1.get()), int(self.param2.get()), int(self.param3.get()),
                int(self.param4.get()), int(self.param5.get()), int(self.param6.get())
            )
            self.log("波形参数设置成功")
        except Exception as e:
            self.log(f"设置波形参数时发生错误: {e}")

        while True:
            try:
                tankhit = int(self.tankhit.get())
                tankdie = int(self.tankdie.get())
                g_force = int(self.g_force.get())
                cur = data_fetcher.run_data_fetcher(tankhit, tankdie, g_force)
                if cur != self.last:
                    m_cur = map_strength(cur)
                    await self.dglab_instance.set_strength_sync(m_cur, m_cur)
                    self.log(f"更新通道强度：A={m_cur}, B={m_cur}")
                    self.last = cur
            except Exception as e:
                self.log(f"检测或更新强度时发生错误: {e}")
            await asyncio.sleep(1)

    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.thread = threading.Thread(target=self.loop.run_until_complete, args=(self.connect_and_set_strength(),))
        self.thread.start()

    def stop(self):
        if hasattr(self, 'loop'):
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()

def main():
    root = tk.Tk()
    root.geometry("512x200")  # Set default window size
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()