import os
import subprocess
import time
import json
import sys

class MumuController:
    def __init__(self, adb_path="adb", mumu_port="7555"):
        # 尝试在常见的 ADB 安装位置查找
        common_adb_paths = [
            adb_path,
            r"E:\platform-tools-latest-windows\platform-tools\adb.exe",  # 添加你的实际路径
            r"C:\Program Files\Microvirt\MEmu\adb.exe",
            r"C:\Program Files\Nox\bin\nox_adb.exe",
            r"C:\Program Files (x86)\MuMu\emulator\nemu\vmonitor\bin\adb_server.exe",
            os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Android\Sdk\platform-tools\adb.exe")
        ]
        
        self.adb_path = None
        for path in common_adb_paths:
            if os.path.exists(path):
                self.adb_path = path
                break
        
        if self.adb_path is None:
            print("警告: 未找到adb程序，请确保已经安装ADB并添加到环境变量中")
            print("您可以：")
            print("1. 安装 Android SDK 并将 platform-tools 添加到环境变量")
            print("2. 直接指定 adb.exe 的完整路径，例如：")
            print(r'controller = MumuController(adb_path="C:\path\to\your\adb.exe")')
            raise FileNotFoundError("找不到 adb 程序")
        
        self.mumu_port = mumu_port
        
        # 创建截图文件夹
        self.screenshots_dir = "screenshots"
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
        
        # 保留的最大截图数量
        self.max_screenshots = 10
        
    def check_devices(self):
        """检查已连接的设备"""
        try:
            cmd = f"{self.adb_path} devices"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print("当前连接的设备：")
            print(result.stdout)
            return "127.0.0.1:" + self.mumu_port in result.stdout
        except Exception as e:
            print(f"检查设备时出错: {e}")
            return False

    def connect_to_mumu(self):
        """连接到MuMu模拟器"""
        try:
            # 确保ADB服务器正在运行
            subprocess.run([self.adb_path, "start-server"])
            
            # 检查是否已经连接
            if self.check_devices():
                print("模拟器已经连接")
                return True
            
            # 连接到模拟器
            connect_cmd = f"{self.adb_path} connect 127.0.0.1:{self.mumu_port}"
            result = subprocess.run(connect_cmd, shell=True, capture_output=True, text=True)
            
            if "connected" in result.stdout.lower():
                print("成功连接到MuMu模拟器")
                return True
            else:
                print("连接失败，请确保MuMu模拟器正在运行")
                return False
        except subprocess.SubprocessError as e:
            print(f"连接过程中出现错误: {e}")
            return False
        except Exception as e:
            print(f"发生未知错误: {e}")
            return False
                
    def tap(self, x, y):
        """模拟点击屏幕"""
        cmd = f"{self.adb_path} -s 127.0.0.1:{self.mumu_port} shell input tap {x} {y}"
        subprocess.run(cmd, shell=True)
        
    def swipe(self, x1, y1, x2, y2, duration=1000):
        """模拟滑动屏幕"""
        cmd = f"{self.adb_path} -s 127.0.0.1:{self.mumu_port} shell input swipe {x1} {y1} {x2} {y2} {duration}"
        subprocess.run(cmd, shell=True)

    def clean_screenshots(self):
        """清理旧的截图文件"""
        try:
            screenshots = [f for f in os.listdir(self.screenshots_dir) if f.endswith('.png')]
            screenshots.sort(key=lambda x: os.path.getmtime(os.path.join(self.screenshots_dir, x)))
            
            # 如果截图数量超过限制，删除最旧的
            while len(screenshots) >= self.max_screenshots:
                oldest = screenshots.pop(0)
                os.remove(os.path.join(self.screenshots_dir, oldest))
                print(f"删除旧截图: {oldest}")
        except Exception as e:
            print(f"清理截图失败: {e}")

    def screenshot(self):
        """获取屏幕截图"""
        try:
            start_time = time.time()
            
            # 生成新截图的文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"screen_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_name)
            
            # 在模拟器中截图并直接拉取到本地
            cmd = f"{self.adb_path} -s 127.0.0.1:{self.mumu_port} exec-out screencap -p > {screenshot_path}"
            subprocess.run(cmd, shell=True)
            
            end_time = time.time()
            print(f"截图耗时: {end_time - start_time:.2f}秒")
            
            return screenshot_path
        except Exception as e:
            print(f"截图失败: {e}")
            return None

    def find_image(self, template_path, threshold=0.8):
        """在屏幕上查找指定图片的位置"""
        try:
            import cv2
            import numpy as np
            
            print(f"开始查找图片: {template_path}")
            start_time = time.time()
            
            # 获取屏幕截图
            screenshot_path = self.screenshot()
            if not screenshot_path:
                return None
            
            # 读取图片
            screen = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if template is None:
                print(f"无法读取模板图片: {template_path}")
                return None
            
            # 模板匹配
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            end_time = time.time()
            print(f"图片查找耗时: {end_time - start_time:.2f}秒, 匹配度: {max_val:.2f}")
            
            if max_val >= threshold:
                # 返回中心点坐标
                w, h = template.shape[1], template.shape[0]
                return (max_loc[0] + w//2, max_loc[1] + h//2)
            return None
        except Exception as e:
            print(f"查找图片失败: {e}")
            return None

    def click_image(self, template_path, threshold=0.8):
        """点击屏幕上的指定图片"""
        pos = self.find_image(template_path, threshold)
        if pos:
            print(f"找到图片，点击位置: {pos}")
            self.tap(pos[0], pos[1])
            return True
        print(f"未找到图片: {template_path}")
        return False

    def capture_template(self, name, x1, y1, x2, y2):
        """截取指定区域作为模板图片"""
        try:
            import cv2
            
            # 先截取整个屏幕
            screenshot_path = self.screenshot()
            if not screenshot_path:
                return False
            
            # 读取并裁剪图片
            screen = cv2.imread(screenshot_path)
            template = screen[y1:y2, x1:x2]
            
            # 确保 images 文件夹存在
            if not os.path.exists("images"):
                os.makedirs("images")
            
            # 保存模板图片
            save_path = os.path.join("images", f"{name}.png")
            cv2.imwrite(save_path, template)
            print(f"模板图片已保存到: {save_path}")
            
            # 保存预览图到screenshots文件夹
            preview = screen.copy()
            cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)
            preview_path = os.path.join(self.screenshots_dir, f"preview_{name}.png")
            cv2.imwrite(preview_path, preview)
            print(f"预览图片已保存到: {preview_path}")
            
            return True
        except Exception as e:
            print(f"保存模板图片失败: {e}")
            return False

class GameAutomation:
    def __init__(self):
        """初始化游戏自动化控制器"""
        try:
            # 获取配置文件路径
            try:
                config_dir = os.path.expanduser("~/.e7auto")
                print(f"配置目录: {config_dir}")
                
                if not os.path.exists(config_dir):
                    print("创建配置目录...")
                    os.makedirs(config_dir)
                    
                config_file = os.path.join(config_dir, "config.json")
                print(f"配置文件路径: {config_file}")
                
            except Exception as e:
                print(f"创建配置目录失败: {e}")
                config_file = "config.json"
                print(f"使用当前目录的配置文件: {config_file}")

            # 尝试加载配置文件
            if os.path.exists(config_file):
                try:
                    print("读取现有配置文件...")
                    with open(config_file, "r") as f:
                        config = json.load(f)
                        saved_path = config.get("adb_path")
                        # 如果是相对路径，转换为绝对路径
                        if saved_path and not os.path.isabs(saved_path):
                            self.adb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), saved_path)
                        else:
                            self.adb_path = saved_path
                        # 检查路径是否指向临时目录
                        if self.adb_path and "\\Temp\\_MEI" in self.adb_path:
                            print("检测到临时目录的ADB路径，重置配置")
                            self.adb_path = None
                    print(f"已读取ADB路径: {self.adb_path}")
                except Exception as e:
                    print(f"读取配置文件失败: {e}")
                    self.adb_path = None
            else:
                print("配置文件不存在，使用默认配置")
                self.adb_path = None

            # 如果没有有效的ADB路径，使用默认路径
            if not self.adb_path or not os.path.exists(self.adb_path):
                print("使用默认ADB路径")
                # 获取程序运行目录
                exe_dir = os.path.dirname(os.path.abspath(__file__))
                if hasattr(sys, '_MEIPASS'):  # 如果是打包后的程序
                    exe_dir = os.path.dirname(sys.executable)
                
                # 使用相对于程序运行目录的adb路径
                self.adb_path = os.path.join(exe_dir, "adb", "adb.exe")
                print(f"设置ADB路径为: {self.adb_path}")
                
                # 保存默认配置
                try:
                    print(f"保存配置到: {config_file}")
                    # 总是保存相对路径
                    save_path = os.path.join("adb", "adb.exe")
                    with open(config_file, "w") as f:
                        json.dump({"adb_path": save_path}, f, indent=2)
                    print("配置保存成功")
                except Exception as e:
                    print(f"保存配置文件失败: {e}")

            # 检查 ADB 路径是否有效
            if not os.path.exists(self.adb_path):
                raise ValueError(f"ADB路径无效: {self.adb_path}")

            print(f"最终使用的ADB路径: {self.adb_path}")

            # 创建控制器
            self.controller = MumuController(adb_path=self.adb_path)
            self.max_energy_purchase = 3  # 默认体力购买次数上限
            self.running = True

            self.screen_center = (360, 640)
            self.energy_purchase_count = 0

            print(f"初始化完成，屏幕中心点设置为: {self.screen_center}")
            print(f"体力购买上限设置为: {self.max_energy_purchase} 次")
            
            # 清理screenshots文件夹
            self.clean_screenshots_folder()

        except Exception as e:
            print(f"初始化过程中发生错误: {e}")
            import traceback
            print(traceback.format_exc())
            raise ValueError(f"初始化失败: {str(e)}")
        
        self.running = True  # 添加运行状态标志
        
    def clean_screenshots_folder(self):
        """清理screenshots文件夹中的所有图片"""
        try:
            screenshots_dir = "screenshots"
            if os.path.exists(screenshots_dir):
                for file in os.listdir(screenshots_dir):
                    if file.endswith('.png'):
                        file_path = os.path.join(screenshots_dir, file)
                        os.remove(file_path)
                print("清理screenshots文件夹完成")
        except Exception as e:
            print(f"清理screenshots文件夹失败: {e}")

    def stop(self):
        """停止所有操作"""
        self.running = False
        
    def find_image(self, template_path, threshold=0.8):
        """在屏幕上查找指定图片的位置"""
        if not self.running:
            return None
        return self.controller.find_image(template_path, threshold)
        
    def check_and_click(self, image_num, max_retries=3, interval=1.0):
        """检查并点击指定编号的图片"""
        for retry in range(max_retries):
            if not self.running:
                return False
            if self.controller.click_image(f"images/{image_num}.png"):
                return True
            time.sleep(interval)
        return False
    
    def find_and_enter_stage(self):
        """找到并进入副本"""
        print("开始寻找副本...")
        # 按顺序点击1-6号图片进入副本
        for i in range(1, 7):
            if not self.check_and_click(i):
                print(f"找不到图片 {i}，副本进入失败")
                return False
            time.sleep(2)
        print("成功进入副本")
        return True
    
    def handle_battle(self):
        """处理战斗过程"""
        print("开始战斗...")
        check_count = 0
        while True:
            # 每5秒检查一次图片7
            print("检查图片7...")
            if self.controller.find_image("images/7.png"):
                print(f"战斗结束，共检查了 {check_count} 次")
                self.check_and_click(7)
                time.sleep(1)
                self.check_and_click(8)
                break
            
            check_count += 1
            time.sleep(5)  # 直接等待5秒再检查
    
    def handle_energy_check(self):
        """处理体力不足的情况"""
        # 检查是否出现图片12（体力不足）
        if self.controller.find_image("images/12.png"):
            print(f"发现体力不足提示（当前已购买 {self.energy_purchase_count} 次）")
            
            # 检查是否超过购买次数限制
            if self.energy_purchase_count >= self.max_energy_purchase:
                print(f"已达到体力购买上限 {self.max_energy_purchase} 次，程序结束")
                return False
                
            # 购买体力
            print(f"购买体力，第 {self.energy_purchase_count + 1} 次")
            
            # 多次尝试点击购买按钮，确保点击成功
            max_retry = 3
            for retry in range(max_retry):
                if self.check_and_click(12):
                    print(f"点击购买按钮成功，等待确认")
                    time.sleep(2)  # 等待购买确认界面
                    
                    # 这里可能需要点击确认购买的按钮
                    # 如果有确认购买的图片，可以添加相应的检查和点击
                    
                    self.energy_purchase_count += 1
                    time.sleep(3)  # 等待购买完成和界面刷新
                    
                    # 再次点击图片6开始副本
                    print("重新点击图片6开始副本")
                    if not self.check_and_click(6):
                        print("点击图片6失败，重试...")
                        continue
                        
                    return True
                else:
                    print(f"第 {retry + 1} 次点击购买按钮失败")
                    time.sleep(1)
            
            print("多次尝试购买体力失败")
            return False
                
        return True

    def handle_stage_end(self):
        """处理副本结束"""
        print("检查副本结束状态...")
        # 检查是否出现图片9
        if self.controller.find_image("images/9.png"):
            print("发现图片9")
            self.check_and_click(9)
            time.sleep(1)
            
        # 检查是否出现图片10
        if self.controller.find_image("images/10.png"):
            print("发现图片10")
            self.check_and_click(10)
            time.sleep(1)
            
        # 检查是否出现图片11（重新开始）
        if self.controller.find_image("images/11.png"):
            print("发现图片11，准备重新开始")
            self.check_and_click(11)
            time.sleep(2)
            
            # 点击图片5
            print("点击图片5")
            if not self.check_and_click(5):
                return False
            time.sleep(2)
            
            # 点击图片6开始新的副本
            print("点击图片6开始新的副本")
            if not self.check_and_click(6):
                return False
                
            # 等待足够的时间让体力不足提示显示出来
            time.sleep(3)  # 增加等待时间
            
            # 处理可能的体力不足情况
            if not self.handle_energy_check():
                return False
                
            return True
            
        return False
    
    def run_auto_battle(self):
        """运行自动战斗"""
        try:
            print("开始自动战斗程序")
            print(f"体力购买次数限制: {self.max_energy_purchase}")
            
            # 清理旧的截图
            self.clean_screenshots_folder()
            
            # 首次进入副本
            if not self.find_and_enter_stage():
                return
                
            # 首次检查体力
            if not self.handle_energy_check():
                return
            
            # 无限循环执行副本
            while True:
                # 处理战斗过程
                self.handle_battle()
                
                # 处理副本结束
                if self.handle_stage_end():
                    print("重新开始副本")
                    time.sleep(2)
                else:
                    print("未检测到重新开始按钮，继续检查")
                
        except KeyboardInterrupt:
            print(f"\n程序被用户中断，共购买体力 {self.energy_purchase_count} 次")
        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            print(f"自动战斗程序结束，共购买体力 {self.energy_purchase_count} 次")
            # 程序结束时也清理截图
            self.clean_screenshots_folder()

if __name__ == "__main__":
    game = GameAutomation()
    
    # 确保成功连接模拟器
    if game.controller.connect_to_mumu():
        print("成功连接模拟器，开始自动战斗")
        game.run_auto_battle()
    else:
        print("连接模拟器失败，请检查模拟器是否正常运行")