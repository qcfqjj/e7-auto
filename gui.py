import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from game_automation import GameAutomation
import threading
import time
import sys
import subprocess

class AutoGameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("第七史诗自动化控制面板")
        self.root.geometry("1100x600")  # 增加窗口大小
        
        # 常见模拟器端口
        self.port_options = {
            "MuMu模拟器(7555)": "7555",
            "雷电模拟器(5555)": "5555",
            "夜神模拟器(62001)": "62001",
            "逍遥模拟器(21503)": "21503",
            "蓝叠模拟器(5555)": "5555",
        }
        
        # 加载配置
        self.load_config()
        
        # 清理screenshots文件夹
        self.clean_screenshots_folder()
        
        # 设置主题样式
        style = ttk.Style()
        style.configure("Title.TLabel", font=("微软雅黑", 12, "bold"))
        style.configure("Content.TLabel", font=("微软雅黑", 10))
        style.configure("Action.TButton", font=("微软雅黑", 10), padding=5)
        
        # 加载副本配置
        self.load_configs()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建左右分栏
        self.left_frame = ttk.Frame(self.main_frame, padding="5")
        self.left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        self.right_frame = ttk.Frame(self.main_frame, padding="5")
        self.right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 在左侧创建控制区域
        self.create_left_panel()
        # 在右侧创建日志区域
        self.create_right_panel()
        
        # 配置列权重
        self.main_frame.columnconfigure(0, weight=1)  # 左侧面板
        self.main_frame.columnconfigure(1, weight=1)  # 右侧面板
        
        self.game = None
        self.running = False  # 添加运行状态标志
        
        # 配置根窗口的grid权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def get_resource_path(self, relative_path):
        """获取资源文件的绝对路径"""
        try:
            # PyInstaller创建临时文件夹,将路径存储在_MEIPASS中
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
        
    def load_configs(self):
        """加载副本配置"""
        self.configs = {}
        config_file = self.get_resource_path("stage_configs.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.configs = json.load(f)
                # 验证配置格式
                if not all("steps" in config for config in self.configs.values()):
                    raise ValueError("配置格式不正确")
            except:
                # 如果配置文件有问题，使用空配置
                os.remove(config_file)
                self.configs = {}
        
        # 保存配置（即使是空的）
        self.save_configs()
        
    def save_configs(self):
        """保存副本配置"""
        with open("stage_configs.json", 'w', encoding='utf-8') as f:
            json.dump(self.configs, f, ensure_ascii=False, indent=2)
            
    def create_left_panel(self):
        """创建左侧控制面板"""
        # 标题
        title_label = ttk.Label(
            self.left_frame, 
            text="第七史诗自动化控制面板", 
            style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 创建各个控制区域
        self.create_adb_connection()
        self.create_stage_selection()
        self.create_energy_settings()
        self.create_control_buttons()
        
    def create_right_panel(self):
        """创建右侧日志面板"""
        # 状态显示区域
        frame = ttk.LabelFrame(self.right_frame, text="运行状态", padding="5")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态文本框
        self.status_text = tk.Text(
            frame, 
            height=35,  # 增加高度
            width=60,   # 增加宽度
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(frame, command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S), pady=5)
        self.status_text['yscrollcommand'] = scrollbar.set
        
        # 配置grid权重
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(0, weight=1)
        
    def create_stage_selection(self):
        """创建副本选择区域"""
        frame = ttk.LabelFrame(self.left_frame, text="副本选择", padding="10")
        frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(frame, text="选择副本:", style="Content.TLabel").grid(row=0, column=0, padx=(0, 10))
        
        self.stage_var = tk.StringVar()
        self.stage_combo = ttk.Combobox(
            frame,
            textvariable=self.stage_var,
            values=list(self.configs.keys()),
            width=30
        )
        self.stage_combo.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Button(frame, text="添加新副本", style="Action.TButton", command=self.add_new_stage).grid(row=0, column=2, padx=(10, 0))
        
    def create_energy_settings(self):
        """创建设置区域"""
        frame = ttk.LabelFrame(self.left_frame, text="运行设置", padding="10")
        frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(frame, text="体力购买上限:", style="Content.TLabel").grid(row=0, column=0, padx=(0, 10))
        
        self.energy_var = tk.StringVar(value="3")
        ttk.Entry(frame, textvariable=self.energy_var, width=10).grid(row=0, column=1)
        
        ttk.Label(frame, text="战斗次数:", style="Content.TLabel").grid(row=0, column=2, padx=(20, 10))
        
        self.battle_count_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.battle_count_var, width=10).grid(row=0, column=3)
        
        ttk.Label(frame, text="(0表示无限次)", style="Content.TLabel", foreground="gray").grid(row=0, column=4, padx=(5, 0))
        
    def create_control_buttons(self):
        """创建控制按钮区域"""
        frame = ttk.Frame(self.left_frame)
        frame.grid(row=4, column=0, columnspan=4, pady=(0, 10))
        
        # 开始按钮
        ttk.Button(
            frame,
            text="开始执行",
            style="Action.TButton",
            command=self.start_automation
        ).grid(row=0, column=0, padx=5)
        
        # 停止按钮
        ttk.Button(
            frame,
            text="停止",
            style="Action.TButton",
            command=self.stop_automation
        ).grid(row=0, column=1, padx=5)
        
    def add_new_stage(self):
        """添加新副本配置"""
        dialog = StageConfigDialog(self.root, self)
        self.root.wait_window(dialog.top)
        
    def start_automation(self):
        """开始自动化执行"""
        if not self.adb_path:
            messagebox.showerror("错误", "请先配置 ADB 路径")
            self.show_adb_config_dialog()
            return
        
        if self.running:
            messagebox.showwarning("警告", "任务正在运行中")
            return
        
        stage = self.stage_var.get()
        if not stage:
            messagebox.showerror("错误", "请选择要执行的副本")
            return
        
        try:
            energy_limit = int(self.energy_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入正确的体力购买上限")
            return
        
        # 获取副本配置
        stage_config = self.configs.get(stage)
        if not stage_config:
            messagebox.showerror("错误", "无效的副本配置")
            return
        
        try:
            # 获取ADB完整路径
            adb_path = self.get_adb_path()
            # 获取选择的端口
            selected_port = self.port_options[self.port_var.get()]
            
            # 创建游戏控制器
            self.game = GameAutomation()
            # 设置ADB路径和模拟器端口
            self.game.controller.adb_path = adb_path  # 确保GameAutomation类支持设置adb_path
            self.game.controller.mumu_port = selected_port
            self.game.max_energy_purchase = energy_limit
            
            # 设置运行状态
            self.running = True
            
            # 在新线程中运行自动化任务
            self.automation_thread = threading.Thread(
                target=self.run_automation,
                args=(stage_config,)
            )
            self.automation_thread.daemon = True
            self.automation_thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")
            self.running = False
        
    def run_automation(self, config):
        """执行自动化任务"""
        try:
            # 获取战斗次数限制
            try:
                battle_limit = int(self.battle_count_var.get())
                current_battles = 0
            except ValueError:
                battle_limit = 0
            
            self.update_status(f"战斗次数限制: {battle_limit if battle_limit > 0 else '无限'}")
            
            # 打印配置内容，帮助调试
            self.update_status("当前配置:")
            self.update_status(str(config))
            
            # 确保成功连接模拟器
            if not self.game.controller.connect_to_mumu():
                self.update_status("连接模拟器失败，请检查模拟器是否正常运行")
                return
            
            self.update_status("开始执行自动化任务")
            
            # 检查配置格式
            if "steps" not in config:
                self.update_status("错误: 配置格式不正确，缺少 'steps' 字段")
                return
            
            # 首次进入副本
            if not self.execute_enter_sequence(config):
                return
            
            # 首次检查体力并计入战斗次数
            current_battles += 1
            self.update_status(f"开始第 {current_battles} 次战斗")
            
            # 无限循环执行副本
            while self.running:
                # 检查是否达到战斗次数限制
                if battle_limit > 0 and current_battles >= battle_limit:
                    self.update_status(f"已达到战斗次数限制: {battle_limit}")
                    break
                
                if not self.execute_battle_sequence(config):
                    break
                
                if not self.execute_end_sequence(config):
                    break
                
                # 准备下一次战斗
                current_battles += 1
                self.update_status(f"开始第 {current_battles} 次战斗")
            
        except Exception as e:
            self.update_status(f"发生错误: {e}")
            import traceback
            self.update_status(traceback.format_exc())
        finally:
            self.running = False  # 确保状态被重置
            self.update_status(f"自动化任务结束，共完成 {current_battles} 次战斗")
        
    def update_status(self, message, debug=False):
        """更新状态显示
        Args:
            message: 状态信息
            debug: 是否为调试信息，True时不显示
        """
        if not debug:  # 只显示非调试信息
            self.status_text.insert(tk.END, f"{message}\n")
            self.status_text.see(tk.END)
        
    def execute_enter_sequence(self, config):
        """执行进入副本序列"""
        for step in config["steps"]:
            if step["type"] == "enter":
                self.update_status("开始进入副本...")
                for action in step["actions"]:
                    if action["action"] == "click":
                        if not self.game.check_and_click(action["image"]):
                            self.update_status(f"点击图片 {action['image']} 失败")
                            return False
                        time.sleep(action.get("wait", 1))
        return True
        
    def execute_battle_sequence(self, config):
        """执行战斗过程"""
        for step in config["steps"]:
            if step["type"] == "battle":
                self.update_status("检查战斗状态...")
                check_count = 0
                while self.running:
                    if not self.running:
                        return False
                    
                    # 检查多个可能的结果
                    if "images" in step["check"]:
                        for check_info in step["check"]["images"]:
                            if self.game.controller.find_image(f"images/{check_info['image']}.png"):
                                result_type = check_info["type"]
                                self.update_status(f"战斗{result_type}结束")
                                
                                wait_time = check_info.get('wait_after_check', 2)
                                self.update_status(f"等待 {wait_time} 秒后继续...", debug=True)  # 调试信息
                                time.sleep(wait_time)
                                
                                actions = step["actions"].get(result_type, [])
                                for action in actions:
                                    if not self.running:
                                        return False
                                    if action["action"] == "click":
                                        self.game.check_and_click(action["image"])
                                        time.sleep(action.get("wait", 1))
                                return True
                                
                    # 原有的单图片检查逻辑
                    elif self.game.controller.find_image(f"images/{step['check']['image']}.png"):
                        self.update_status("战斗结束")
                        wait_time = step['check'].get('wait_after_check', 2)
                        self.update_status(f"等待 {wait_time} 秒后继续...")
                        time.sleep(wait_time)
                        
                        for action in step["actions"]:
                            if not self.running:
                                return False
                            if action["action"] == "click":
                                self.game.check_and_click(action["image"])
                                time.sleep(action.get("wait", 1))
                        return True
                        
                    check_count += 1
                    time.sleep(step["check"].get("interval", 5))
        return True
        
    def execute_end_sequence(self, config):
        """执行结算和重新开始序列"""
        for step in config["steps"]:
            if not self.running:
                return False
            
            if step["type"] in ["end", "restart"]:
                for action in step["actions"]:
                    if not self.running:
                        return False
                    if action["action"] == "click":
                        if self.game.controller.find_image(f"images/{action['image']}.png"):
                            self.update_status(f"点击图片 {action['image']}", debug=True)  # 调试信息
                            self.game.check_and_click(action["image"])
                            time.sleep(action.get("wait", 1))
        
            elif step["type"] == "energy":
                if not self.running:
                    return False
                if self.game.controller.find_image(f"images/{step['check']['image']}.png"):
                    if not self.game.handle_energy_check():
                        return False
        return True
        
    def stop_automation(self):
        """停止自动化执行"""
        if not self.running:
            return
        
        self.update_status("正在停止任务...")
        self.running = False
        
        # 停止游戏控制器
        if self.game:
            self.game.stop()
        
        try:
            # 等待线程结束
            if self.automation_thread and self.automation_thread.is_alive():
                self.automation_thread.join(timeout=2)
                
                # 如果线程还在运行，强制结束
                if self.automation_thread.is_alive():
                    self.update_status("强制停止任务")
                    
        except Exception as e:
            self.update_status(f"停止任务时出错: {e}")
        finally:
            self.running = False
            self.update_status("任务已停止")
        
    def run(self):
        self.root.mainloop()

    def clean_screenshots_folder(self):
        """清理screenshots文件夹"""
        try:
            screenshots_dir = "screenshots"
            if os.path.exists(screenshots_dir):
                for file in os.listdir(screenshots_dir):
                    try:
                        file_path = os.path.join(screenshots_dir, file)
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"删除文件失败 {file}: {e}")
        except Exception as e:
            print(f"清理screenshots文件夹失败: {e}")

    def get_config_path(self):
        """获取配置文件路径"""
        try:
            # 尝试使用用户目录
            config_dir = os.path.expanduser("~/.e7auto")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            config_path = os.path.join(config_dir, "config.json")
            print(f"使用配置文件路径: {config_path}")
            return config_path
        except Exception as e:
            print(f"无法使用用户目录: {e}")
            # 如果无法使用用户目录，则使用当前目录
            config_path = "config.json"
            print(f"回退到当前目录: {config_path}")
            return config_path

    def load_adb_path(self):
        """加载 ADB 路径配置"""
        config_file = self.get_config_path()
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    adb_path = config.get("adb_path")
                    if adb_path and os.path.exists(adb_path):
                        return adb_path
            except:
                pass
        # 如果没有配置或配置无效，尝试使用内置ADB
        self.use_builtin_adb(silent=True)
        return self.adb_path

    def save_adb_path(self, path):
        """保存 ADB 路径配置"""
        config_file = self.get_config_path()
        try:
            config = {"adb_path": path}
            with open(config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败：{e}")

    def use_builtin_adb(self, silent=False):
        """使用内置的ADB"""
        try:
            self.adb_path = "adb/adb.exe"
            self.adb_path_var.set(self.adb_path)
            self.save_config()
            if not silent:
                messagebox.showinfo("成功", "已配置内置ADB")
            return True
        except Exception as e:
            if not silent:
                messagebox.showerror("错误", f"使用内置ADB失败: {str(e)}")
            return False

    def show_adb_config_dialog(self):
        """显示 ADB 配置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("ADB 配置")
        dialog.geometry("500x300")
        
        # 说明文字
        ttk.Label(
            dialog,
            text="请配置 ADB 路径，推荐使用内置ADB：\n" +
                 "1. 使用内置的 ADB（推荐）\n" +
                 "2. 选择已安装的 ADB\n" +
                 "3. 手动指定 ADB 路径",
            style="Content.TLabel"
        ).pack(pady=10)
        
        def use_builtin_adb():
            """使用内置的 ADB"""
            try:
                # 获取当前目录下的adb文件夹
                builtin_adb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adb")
                adb_exe_path = os.path.join(builtin_adb_dir, "adb.exe")
                
                if not os.path.exists(adb_exe_path):
                    messagebox.showerror("错误", "未找到内置的 ADB 文件，请确保 adb 文件夹包含所需文件")
                    return
                    
                # 检查必要的文件是否存在
                required_files = ["AdbWinApi.dll", "AdbWinUsbApi.dll"]
                missing_files = [f for f in required_files 
                                if not os.path.exists(os.path.join(builtin_adb_dir, f))]
                
                if missing_files:
                    messagebox.showerror("错误", f"缺少以下文件：\n{', '.join(missing_files)}")
                    return
                    
                # 使用内置 ADB 的路径
                self.adb_path = adb_exe_path
                self.adb_path_var.set(self.adb_path)  # 更新显示
                self.save_adb_path(self.adb_path)
                messagebox.showinfo("成功", "已配置为内置ADB")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("错误", f"配置内置 ADB 失败：{e}")
        
        def browse_adb():
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                title="选择 adb.exe",
                filetypes=[("ADB 执行文件", "adb.exe")]
            )
            if path:
                self.adb_path = path
                self.adb_path_var.set(path)  # 更新显示
                self.save_adb_path(path)
                dialog.destroy()
        
        # 创建按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        # 内置ADB按钮（大一点，更显眼）
        ttk.Button(
            button_frame,
            text="使用内置 ADB（推荐）",
            command=use_builtin_adb,
            style="Action.TButton",
            width=25
        ).pack(pady=10)
        
        # 其他按钮
        ttk.Button(
            button_frame,
            text="手动选择ADB",
            command=browse_adb,
            width=20
        ).pack(pady=5)
        
        # 自动尝试使用内置ADB
        dialog.after(500, use_builtin_adb)

    def create_adb_connection(self):
        """创建ADB连接区域"""
        frame = ttk.LabelFrame(self.left_frame, text="ADB连接", padding="5")
        frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # ADB路径显示和按钮
        ttk.Label(frame, text="ADB路径:", style="Content.TLabel").grid(row=0, column=0, padx=(5, 10))
        
        self.adb_path_var = tk.StringVar(value=self.adb_path or "未配置")
        ttk.Entry(frame, textvariable=self.adb_path_var, state="readonly", width=35).grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(frame, text="配置ADB", style="Action.TButton", command=self.show_adb_config_dialog).grid(row=0, column=3, padx=(10, 0))
        ttk.Button(frame, text="使用内置ADB", style="Action.TButton", command=self.use_builtin_adb).grid(row=0, column=4, padx=(10, 0))
        
        # 模拟器选择
        ttk.Label(frame, text="模拟器:", style="Content.TLabel").grid(row=1, column=0, padx=(0, 10), pady=(5, 0))
        
        self.port_var = tk.StringVar(value=self.selected_emulator)
        port_combo = ttk.Combobox(
            frame,
            textvariable=self.port_var,
            values=list(self.port_options.keys()),
            state="readonly",
            width=20
        )
        port_combo.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(frame, text="检查连接", style="Action.TButton", command=self.check_emulator_connection).grid(row=1, column=2, padx=(10, 0), pady=(5, 0))

    def check_emulator_connection(self):
        """检查模拟器连接状态"""
        if not self.adb_path:
            messagebox.showerror("错误", "请先配置ADB路径")
            return
        
        try:
            # 获取ADB完整路径
            adb_path = self.get_adb_path()
            # 获取选择的端口
            selected_port = self.port_options[self.port_var.get()]
            
            # 先列出所有连接的设备
            cmd = f'"{adb_path}" devices'  # 添加引号避免路径空格问题
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            devices = result.stdout.strip().split('\n')[1:]  # 跳过第一行
            
            # 显示检测到的设备
            device_info = "检测到的模拟器实例:\n"
            found_devices = []
            
            for device in devices:
                if device.strip():
                    device_id = device.split()[0]
                    if ':' in device_id:  # 模拟器
                        port = device_id.split(':')[1]
                        # 尝试获取设备信息
                        try:
                            info_cmd = f"{adb_path} -s {device_id} shell getprop ro.product.model"
                            info = subprocess.run(info_cmd, shell=True, capture_output=True, text=True)
                            model = info.stdout.strip() or "未知设备"
                            device_info += f"端口 {port}: {model}\n"
                            found_devices.append(port)
                        except:
                            device_info += f"端口 {port}: 无法获取信息\n"
            
            if not found_devices:
                device_info += "未检测到任何模拟器实例\n"
            
            # 显示当前选择的端口
            device_info += f"\n当前选择的端口: {selected_port}"
            if selected_port in found_devices:
                device_info += " (已连接)"
            else:
                device_info += " (未连接)"
            
            # 显示设备信息
            messagebox.showinfo("模拟器状态", device_info)
            
            # 尝试连接选择的端口
            cmd = f'"{adb_path}" connect 127.0.0.1:{selected_port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if "connected" in result.stdout.lower():
                messagebox.showinfo("成功", f"成功连接到端口 {selected_port} 的模拟器")
            else:
                messagebox.showerror("错误", f"无法连接到端口 {selected_port} 的模拟器")
            
        except Exception as e:
            messagebox.showerror("错误", f"连接检查失败: {str(e)}")

    def load_config(self):
        """加载配置"""
        try:
            config_file = "config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # 始终使用相对路径
                    self.adb_path = "adb/adb.exe"
                    # 加载选择的模拟器端口
                    saved_port = config.get("emulator_port")
                    if saved_port:
                        for name, port in self.port_options.items():
                            if port == saved_port:
                                self.selected_emulator = name
                                break
                    else:
                        self.selected_emulator = "MuMu模拟器(7555)"
            else:
                # 默认使用相对路径
                self.adb_path = "adb/adb.exe"
                self.selected_emulator = "MuMu模拟器(7555)"
                # 保存默认配置
                self.save_config()
        except:
            self.adb_path = "adb/adb.exe"
            self.selected_emulator = "MuMu模拟器(7555)"

    def save_config(self):
        """保存配置"""
        try:
            config_file = "config.json"
            config = {
                "adb_path": "adb/adb.exe",  # 始终保存相对路径
                "emulator_port": self.port_options[self.port_var.get()]
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{e}")

    def on_closing(self):
        """窗口关闭时的处理"""
        try:
            # 如果正在运行，先停止
            if self.running:
                self.stop_automation()
            
            # 清理截图文件夹
            self.clean_screenshots_folder()
            
            # 关闭窗口
            self.root.destroy()
        except Exception as e:
            print(f"关闭时出错: {e}")
            self.root.destroy()

    def get_adb_path(self):
        """获取ADB的完整路径"""
        if self.adb_path == "adb/adb.exe":
            # 如果是相对路径，转换为完整路径
            return os.path.abspath(self.adb_path)
        return self.adb_path

class StageConfigDialog:
    """副本配置对话框"""
    def __init__(self, parent, gui):
        self.top = tk.Toplevel(parent)
        self.gui = gui
        self.top.title("添加新副本")
        
        # 副本名称
        ttk.Label(self.top, text="副本名称:").grid(row=0, column=0, padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(self.top, textvariable=self.name_var).grid(row=0, column=1, padx=5, pady=5)
        
        # 副本描述
        ttk.Label(self.top, text="副本描述:").grid(row=1, column=0, padx=5, pady=5)
        self.desc_var = tk.StringVar()
        ttk.Entry(self.top, textvariable=self.desc_var).grid(row=1, column=1, padx=5, pady=5)
        
        # 确定按钮
        ttk.Button(
            self.top,
            text="确定",
            command=self.save_config
        ).grid(row=2, column=0, columnspan=2, pady=10)
        
    def save_config(self):
        name = self.name_var.get()
        desc = self.desc_var.get()
        if name:
            # 使用新的配置格式
            self.gui.configs[name] = {
                "description": desc or "新副本",
                "steps": [
                    # 进入副本
                    {
                        "type": "enter",
                        "actions": [
                            {"action": "click", "image": i, "wait": 2}
                            for i in range(1, 7)
                        ]
                    },
                    # 战斗检查
                    {
                        "type": "battle",
                        "check": {"image": 7, "interval": 5},
                        "actions": [
                            {"action": "click", "image": 7, "wait": 1},
                            {"action": "click", "image": 8, "wait": 1}
                        ]
                    },
                    # 结算
                    {
                        "type": "end",
                        "actions": [
                            {"action": "click", "image": 9, "wait": 1},
                            {"action": "click", "image": 10, "wait": 1}
                        ]
                    },
                    # 重新开始
                    {
                        "type": "restart",
                        "actions": [
                            {"action": "click", "image": 11, "wait": 2},
                            {"action": "click", "image": 5, "wait": 2},
                            {"action": "click", "image": 6, "wait": 3}
                        ]
                    },
                    # 体力检查
                    {
                        "type": "energy",
                        "check": {"image": 12},
                        "actions": [
                            {"action": "handle_energy"}
                        ]
                    }
                ]
            }
            self.gui.save_configs()
            self.gui.stage_combo['values'] = list(self.gui.configs.keys())
            self.top.destroy()

if __name__ == "__main__":
    gui = AutoGameGUI()
    gui.run() 