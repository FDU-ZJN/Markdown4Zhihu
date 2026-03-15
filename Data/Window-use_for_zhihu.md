---
title: Window_use环境配置和UI编写
date: 2025-10-25 14:46:07
categories: 计算机
tags:
  - LLM
  - Windows
cover: /img/cover_15.jpg
highlight_shrink: false
abbrlink: 2274654979
---

原项目地址：https://github.com/CursorTouch/Windows-Use.git
		有趣的玩具，自己写了个小ui，他llm跟gui层的Windows接起来还是很有意思的，允许AI**直接在GUI层面与Windows操作系统交互**。但用起来确实笨笨的，稍微复杂一点就不行了，只能当个玩具了，不过他内层还有不少工具，应该能更深入地开发。

因为国外的API充值要国外的银行卡，我把环境替换成了使用`qwen`。

## 效果

<div style="position:relative; padding-bottom:75%; width:100%; height:0">
    <iframe src="//player.bilibili.com/player.html?bvid=BV1ugsdznEgG&page=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="position:absolute; height: 100%; width: 100%;"></iframe>
</div>

## UI代码

```python
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QLineEdit, QPushButton, QWidget, QLabel, 
                             QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import os
import io

from windows_use.agent import Agent, Browser
from langchain_community.chat_models.tongyi import ChatTongyi 
from dotenv import load_dotenv

load_dotenv()

class AgentWorker(QThread):
    response_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, query, llm):
        super().__init__()
        self.query = query
        self.llm = llm
        self.agent = None

    def _execute_agent(self, query):
        old_stdout = sys.stdout
        stdout_capture = io.StringIO()
        sys.stdout = stdout_capture
        
        try:
            self.agent = Agent(
                llm=self.llm, 
                browser=Browser.EDGE,
                use_vision=False,
                auto_minimize=False
            )
            
            self.agent.print_response(query=query)
            
            output = stdout_capture.getvalue()
            self.response_finished.emit(output)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            sys.stdout = old_stdout

    def run(self):
        try:
            self._execute_agent(query=self.query)
            
        except Exception as e:
            self.error_occurred.emit(f"Agent执行错误: {str(e)}")

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.agent_worker = None
        self.llm = None
        self.init_llm()
        self.init_ui()
    
    def init_llm(self):
            self.llm = ChatTongyi(
                model="qwen-plus",
                temperature=0.2
            )
            
    def init_ui(self):
        self.setWindowTitle("🚀 AI 桌面任务 Agent") 
        self.setGeometry(100, 100, 750, 600)

        self.set_dark_theme()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 30, 30, 20)
        
        title = QLabel("🤖 AI 桌面任务 Agent")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 22, QFont.Bold)) 
        title.setStyleSheet("color: #4CAF50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #3c444f;")
        main_layout.addWidget(title)
        
        response_label = QLabel("💬 Agent 输出日志:")
        response_label.setFont(QFont("Arial", 12, QFont.Bold))
        response_label.setStyleSheet("color: #BBDEFB; margin-top: 5px;")
        main_layout.addWidget(response_label)
        
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a2027;
                color: #e0e0e0;
                border: 1px solid #4a5568;
                border-radius: 12px;
                padding: 15px;
                font-family: 'Segoe UI', 'Consolas', monospace;
                font-size: 10pt;
            }
        """)
        main_layout.addWidget(self.response_text)
        
        input_layout = QHBoxLayout()
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("输入桌面任务，例如：打开记事本，或切换到桌面...")
        self.query_input.setStyleSheet("""
            QLineEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #546e7a;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #4CAF50; }
        """)
        self.query_input.returnPressed.connect(self.execute_query)
        
        button_style_base = """
            border: none;
            border-radius: 10px; 
            padding: 15px 25px;
            font-weight: bold;
            font-size: 14px;
        """
        
        self.send_button = QPushButton("执行 (▶️)")
        self.send_button.setStyleSheet(button_style_base + """
            QPushButton { background-color: #4CAF50; color: white; }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.send_button.clicked.connect(self.execute_query)
        
        self.stop_button = QPushButton("停止 (⏹️)")
        self.stop_button.setEnabled(False) 
        self.stop_button.setStyleSheet(button_style_base + """
            QPushButton { background-color: #F44336; color: white; }
            QPushButton:hover { background-color: #D32F2F; }
            QPushButton:disabled { background-color: #546e7a; color: #a9a9a9; }
        """)
        self.stop_button.clicked.connect(self.stop_agent)
        
        input_layout.addWidget(self.query_input)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.stop_button)
        
        main_layout.addLayout(input_layout)
        
        self.status_label = QLabel(f"状态: {'就绪' if self.llm else 'LLM 错误，请检查配置'}")
        self.status_label.setStyleSheet("color: #a9a9a9; padding: 10px 0 0 0; font-style: italic;")
        main_layout.addWidget(self.status_label)
    
    def set_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #212529; }
            QWidget { background-color: #212529; color: #e0e0e0; }
        """)
        
    def execute_query(self):
        query = self.query_input.text().strip()
        
        if not self.llm:
            QMessageBox.critical(self, "LLM 错误", "LLM 未初始化或配置错误，无法执行任务。")
            return
            
        if not query:
            QMessageBox.warning(self, "输入错误", "请输入查询内容")
            return
            
        self.send_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.query_input.setEnabled(False)
        self.status_label.setText("状态: Agent 任务执行中... (请等待或点击停止)")
        
        self.response_text.clear()
        self.response_text.append(f"<span style='color:#4CAF50; font-weight:bold;'>🤖 [Agent] 任务:</span> {query}\n\n<span style='color:#BBDEFB; font-weight:bold;'>--- 执行日志 ---</span>\n")
        
        self.agent_worker = AgentWorker(query, self.llm)
        
        self.agent_worker.response_finished.connect(self.on_response_finished)
        self.agent_worker.error_occurred.connect(self.on_error_occurred)
        
        self.agent_worker.start()
        
    def stop_agent(self):
        if self.agent_worker and self.agent_worker.isRunning():
            self.agent_worker.terminate()
            self.agent_worker.wait()
            
            self.response_text.append("\n<span style='color:#F44336; font-weight:bold;'>--- 🛑 操作已停止 ---</span>")
            self.status_label.setText("状态: 已停止")
        
        self.send_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.query_input.setEnabled(True)
        self.query_input.setFocus()

    def closeEvent(self, event):
        if self.agent_worker and self.agent_worker.isRunning():
            reply = QMessageBox.question(self, '确认退出',
                "Agent 任务正在运行，确定要关闭并终止任务吗？", 
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.stop_agent()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    
    def on_response_finished(self, response):
        self.response_text.setPlainText(response)
        self.response_text.append("\n<span style='color:#4CAF50; font-weight:bold;'>--- ✅ 任务完成 ---</span>")

        self.status_label.setText("状态: ✅ 任务完成")
        
        self.send_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.query_input.setEnabled(True)
        self.query_input.clear()
        self.query_input.setFocus()
    
    def on_error_occurred(self, error_message):
        self.response_text.append(f"\n<span style='color:#F44336; font-weight:bold;'>--- ❌ 错误 ---</span>\n{error_message}")
        self.status_label.setText("状态: ❌ 错误")
        
        self.send_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.query_input.setEnabled(True)
        self.query_input.setFocus()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion') 
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(33, 37, 41))
    palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.Base, QColor(26, 32, 39))
    palette.setColor(QPalette.AlternateBase, QColor(45, 53, 61))
    palette.setColor(QPalette.ToolTipBase, QColor(224, 224, 224))
    palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
    palette.setColor(QPalette.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.Button, QColor(50, 56, 62))
    palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(76, 175, 80))
    palette.setColor(QPalette.Highlight, QColor(76, 175, 80))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    window = ChatWindow()
    if window.llm:
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

