import os
import sys
import re
import requests
from PyQt5 import QtWidgets, QtGui, QtCore
from netease_music_core import url_v1, name_v1, lyric_v1, save_cookie, load_cookie


def sanitize_filename(filename):
    # 去掉 Windows 不允许的特殊字符
    return re.sub(r'[\\/:*?"<>|]', '', filename)


def download_song(song_url, song_name):
    try:
        if not os.path.exists("download"):
            os.makedirs("download")

        sanitized_song_name = sanitize_filename(song_name)
        response = requests.get(song_url, stream=True)
        response.raise_for_status()
        with open(os.path.join("download", f"{sanitized_song_name}.flac"), "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        QtWidgets.QMessageBox.information(None, "成功", f"歌曲已成功下载：download/{sanitized_song_name}.flac")
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "错误", f"下载失败: {str(e)}")


class MusicInfoApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.song_url = None
        self.song_name = None
        self.song_artist = None
        self.init_ui()

        # 创建一个定时器用于延迟处理ID输入
        self.id_input_timer = QtCore.QTimer()
        self.id_input_timer.setSingleShot(True)
        self.id_input_timer.timeout.connect(self.fetch_song_info)

    def on_song_id_changed(self):
        self.id_input_timer.start(1000)

    def init_ui(self):
        self.setWindowTitle("网易云单曲下载工具")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("background-color: #2E2E2E; color: #FFFFFF;")
        self.setWindowIcon(QtGui.QIcon("163.ico"))

        main_layout = QtWidgets.QHBoxLayout(self)

        left_layout = QtWidgets.QVBoxLayout()

        title_label = QtWidgets.QLabel("网易云单曲下载工具", self)
        title_label.setFont(QtGui.QFont("Helvetica", 22, QtGui.QFont.Bold))
        title_label.setStyleSheet("color: #1DB954; margin-bottom: 20px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        left_layout.addWidget(title_label)

        song_id_card = QtWidgets.QGroupBox("歌曲ID输入", self)
        song_id_card.setStyleSheet("border: 1px solid #1DB954; border-radius: 8px; padding: 10px;")
        song_id_layout = QtWidgets.QHBoxLayout(song_id_card)
        self.song_id_input = QtWidgets.QLineEdit(song_id_card)
        self.song_id_input.setPlaceholderText("请输入歌曲ID")
        self.song_id_input.setStyleSheet("background-color: #404040; color: #FFFFFF; border-radius: 5px; padding: 5px;")
        song_id_layout.addWidget(self.song_id_input)
        left_layout.addWidget(song_id_card)

        quality_cookie_card = QtWidgets.QGroupBox("参数设置", self)
        quality_cookie_card.setStyleSheet("border: 1px solid #1DB954; border-radius: 8px; padding: 10px;")
        quality_cookie_layout = QtWidgets.QFormLayout(quality_cookie_card)
        self.level_input = QtWidgets.QComboBox(quality_cookie_card)
        self.level_input.addItems(
            ["standard (标准音质)", "exhigh (极高音质)", "lossless (无损音质)", "hires (Hi-Res音质)",
             "jyeffect (高清环绕声)", "sky (沉浸环绕声)", "jymaster (超清母带)"])
        self.level_input.setStyleSheet("background-color: #404040; color: #FFFFFF; border-radius: 5px; padding: 5px;")

        self.cookie_input = QtWidgets.QLineEdit(quality_cookie_card)
        self.cookie_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.cookie_input.setStyleSheet("background-color: #404040; color: #FFFFFF; border-radius: 5px; padding: 5px;")

        self.naming_rule_input = QtWidgets.QComboBox(quality_cookie_card)
        self.naming_rule_input.addItems([
            "歌曲名",
            "歌曲名 - 作者",
            "作者 - 歌曲名",
            "自定义"
        ])
        self.naming_rule_input.setStyleSheet(
            "background-color: #404040; color: #FFFFFF; border-radius: 5px; padding: 5px;")

        self.custom_naming_label = QtWidgets.QLabel("自定义格式：", quality_cookie_card)
        self.custom_naming_input = QtWidgets.QLineEdit(quality_cookie_card)
        self.custom_naming_input.setPlaceholderText("例如：{作者} - {歌曲名}")
        self.custom_naming_input.setToolTip("可用占位符: {歌曲名}, {作者}")
        self.custom_naming_input.setStyleSheet(
            "background-color: #404040; color: #FFFFFF; border-radius: 5px; padding: 5px;")

        quality_cookie_layout.addRow("请选择音质级别：", self.level_input)
        quality_cookie_layout.addRow("请输入MUSIC_U：", self.cookie_input)
        quality_cookie_layout.addRow("请选择命名规则：", self.naming_rule_input)
        quality_cookie_layout.addRow(self.custom_naming_label, self.custom_naming_input)
        left_layout.addWidget(quality_cookie_card)

        self.custom_naming_label.setVisible(False)
        self.custom_naming_input.setVisible(False)

        song_info_card = QtWidgets.QGroupBox("歌曲信息", self)
        song_info_card.setStyleSheet("border: 1px solid #1DB954; border-radius: 8px; padding: 10px;")
        song_info_layout = QtWidgets.QVBoxLayout(song_info_card)
        self.result_text = QtWidgets.QTextEdit(song_info_card)
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("background-color: #333333; color: #FFFFFF; border-radius: 5px;")
        song_info_layout.addWidget(self.result_text)
        left_layout.addWidget(song_info_card)

        button_layout = QtWidgets.QHBoxLayout()
        self.download_button = QtWidgets.QPushButton("下载歌曲", self)
        self.download_button.setStyleSheet(
            "background-color: #1DB954; color: white; border-radius: 10px; padding: 10px 20px;")
        self.download_button.setEnabled(False)
        button_layout.addWidget(self.download_button)
        left_layout.addLayout(button_layout)

        main_layout.addLayout(left_layout)

        lyrics_card = QtWidgets.QGroupBox("歌词", self)
        lyrics_card.setStyleSheet("border: 1px solid #1DB954; border-radius: 8px; padding: 10px;")
        lyrics_layout = QtWidgets.QVBoxLayout(lyrics_card)
        self.lyrics_text = QtWidgets.QTextEdit(lyrics_card)
        self.lyrics_text.setReadOnly(True)
        self.lyrics_text.setStyleSheet("background-color: #333333; color: #FFFFFF; border-radius: 5px;")
        lyrics_layout.addWidget(self.lyrics_text)
        main_layout.addWidget(lyrics_card)

        links_layout = QtWidgets.QHBoxLayout()
        github_label = QtWidgets.QLabel("<a href='https://github.com/Hellohistory/OpenPrepTools'>GitHub地址</a>", self)
        github_label.setStyleSheet("color: #1DB954; margin-top: 20px;")
        github_label.setOpenExternalLinks(True)
        links_layout.addWidget(github_label)

        gitee_label = QtWidgets.QLabel("<a href='https://gitee.com/Hellohistory/OpenPrepTools'>Gitee地址</a>", self)
        gitee_label.setStyleSheet("color: #1DB954; margin-top: 20px; margin-left: 20px;")
        gitee_label.setOpenExternalLinks(True)
        links_layout.addWidget(gitee_label)

        left_layout.addLayout(links_layout)

        self.setLayout(main_layout)

        self.song_id_input.textChanged.connect(self.on_song_id_changed)
        self.download_button.clicked.connect(self.download_song_action)
        self.level_input.currentIndexChanged.connect(self.fetch_song_info)
        self.naming_rule_input.currentIndexChanged.connect(self.on_naming_rule_changed)

        self.auto_load_cookie()

    def on_naming_rule_changed(self, index):
        is_custom = (index == 3)
        self.custom_naming_label.setVisible(is_custom)
        self.custom_naming_input.setVisible(is_custom)

    def auto_load_cookie(self):
        try:
            cookie = load_cookie()
            if cookie and "MUSIC_U" in cookie:
                self.cookie_input.setText(cookie["MUSIC_U"])
        except Exception:
            pass  # 找不到文件或文件有问题则忽略

    def fetch_song_info(self):
        song_id = self.song_id_input.text()
        if not song_id:
            return

        level = self.level_input.currentText().split()[0]

        music_u = self.cookie_input.text().strip()
        cookies = {
            "os": "pc",
            "appver": "8.9.70",
            "osver": "",
            "deviceId": "pyncm!"
        }
        if music_u:
            cookies["MUSIC_U"] = music_u
            save_cookie(cookies)

        try:
            url_info = url_v1(song_id, level, cookies)
            song_info = name_v1(song_id)
            lyric_info = lyric_v1(song_id, cookies)

            if 'data' in url_info and url_info['data'] and url_info['data'][0].get('url'):
                song_details = song_info['songs'][0]
                artists = [ar['name'] for ar in song_details.get('ar', [])]

                self.song_url = url_info['data'][0]['url']
                self.song_name = sanitize_filename(song_details['name'])
                self.song_artist = sanitize_filename(", ".join(artists))

                song_lyrics = lyric_info.get('lrc', {}).get('lyric', '无歌词')

                result = f"歌曲名称: {self.song_name}\n作      者: {self.song_artist}\n歌曲链接: {self.song_url}"
                self.result_text.setText(result)
                self.lyrics_text.setText(song_lyrics)
                self.download_button.setEnabled(True)
            else:
                self.download_button.setEnabled(False)
                self.result_text.setText("无法获取歌曲信息，请检查ID、网络或Cookie是否正确。")
                self.lyrics_text.setText("")
                QtWidgets.QMessageBox.critical(self, "错误",
                                               "无法获取歌曲链接信息！\n可能是VIP歌曲需要有效的MUSIC_U，或者ID有误。")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"发生错误: {str(e)}")

    def download_song_action(self):
        if not (self.song_url and self.song_name and self.song_artist):
            QtWidgets.QMessageBox.critical(self, "错误", "无法下载歌曲，请先获取有效的歌曲信息！")
            return

        rule_index = self.naming_rule_input.currentIndex()
        final_song_name = ""

        if rule_index == 0:
            final_song_name = self.song_name
        elif rule_index == 1:
            final_song_name = f"{self.song_name} - {self.song_artist}"
        elif rule_index == 2:
            final_song_name = f"{self.song_artist} - {self.song_name}"
        elif rule_index == 3:
            custom_format = self.custom_naming_input.text()
            if not custom_format:
                QtWidgets.QMessageBox.warning(self, "警告", "自定义命名格式不能为空！")
                return

            final_song_name = custom_format.replace('{歌曲名}', self.song_name).replace('{作者}', self.song_artist)

        if final_song_name:
            download_song(self.song_url, final_song_name)
        else:
            QtWidgets.QMessageBox.critical(self, "错误", "未能生成有效的文件名！")


if __name__ == '__main__':
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)
    music_info_app = MusicInfoApp()
    music_info_app.show()
    sys.exit(app.exec_())