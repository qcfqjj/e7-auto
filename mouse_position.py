import win32gui
import win32api
import win32con
import time
from PIL import ImageGrab
import cv2
import numpy as np

class MousePositionTool:
    def __init__(self):
        self.start_pos = None
        self.window_handle = None
        
    def find_mumu_window(self):
        """查找MuMu模拟器窗口"""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "MuMu" in title:  # 可以根据实际模拟器窗口标题修改
                    windows.append((hwnd, title))
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if not windows:
            print("未找到MuMu模拟器窗口")
            return None
            
        # 如果找到多个窗口，打印出来让用户选择
        if len(windows) > 1:
            print("找到多个MuMu窗口：")
            for i, (hwnd, title) in enumerate(windows):
                print(f"{i+1}. {title}")
            choice = int(input("请选择窗口序号: ")) - 1
            return windows[choice][0]
        
        return windows[0][0]
    
    def on_mouse_event(self):
        """监听鼠标事件"""
        try:
            self.window_handle = self.find_mumu_window()
            if not self.window_handle:
                return
            
            # 获取窗口位置和客户区位置
            window_rect = win32gui.GetWindowRect(self.window_handle)
            client_rect = win32gui.GetClientRect(self.window_handle)
            _, _, client_width, client_height = client_rect
            
            # 计算边框和标题栏的大小
            border_x = ((window_rect[2] - window_rect[0]) - client_width) // 2
            title_y = ((window_rect[3] - window_rect[1]) - client_height) - border_x
            
            print(f"\n请在模拟器窗口内点击，按Ctrl+C退出")
            print("点击左键：获取单点坐标")
            print("拖动左键：获取矩形区域坐标")
            
            while True:
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    # 获取鼠标位置
                    x, y = win32api.GetCursorPos()
                    # 转换为客户区坐标（减去边框和标题栏）
                    client_x = x - window_rect[0] - border_x
                    client_y = y - window_rect[1] - title_y
                    
                    if not self.start_pos:
                        self.start_pos = (client_x, client_y)
                        print(f"\n开始位置: ({client_x}, {client_y})")
                    else:
                        # 截取区域并保存预览
                        self.capture_preview(
                            (window_rect[0] + border_x, 
                             window_rect[1] + title_y, 
                             window_rect[2] - border_x, 
                             window_rect[3] - border_x),
                            self.start_pos, 
                            (client_x, client_y)
                        )
                        print(f"结束位置: ({client_x}, {client_y})")
                        print(f"区域: ({self.start_pos[0]}, {self.start_pos[1]}) -> ({client_x}, {client_y})")
                        self.start_pos = None
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n退出坐标获取工具")
    
    def capture_preview(self, window_rect, start_pos, end_pos):
        """捕获选择区域的预览图"""
        # 截取窗口图像
        screenshot = ImageGrab.grab(window_rect)
        # 转换为opencv格式
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 画矩形
        cv2.rectangle(frame, 
                     (start_pos[0], start_pos[1]), 
                     (end_pos[0], end_pos[1]), 
                     (0, 255, 0), 2)
        
        # 保存预览图
        cv2.imwrite("area_preview.png", frame)
        print("预览图片已保存到: area_preview.png")

if __name__ == "__main__":
    tool = MousePositionTool()
    tool.on_mouse_event() 