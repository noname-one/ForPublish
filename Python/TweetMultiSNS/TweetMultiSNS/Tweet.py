# パッケージの読み込み
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk

# 独自パッケージの読み込み
import sys
import os
if getattr(sys, 'frozen', False):
	# PyInstallerでバンドルされた実行ファイルの場合
	base_path = sys._MEIPASS  # バンドル時の一時ディレクトリ
else:
	# スクリプトを直接実行している場合
	base_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(base_path, '../Common'))
from Tweet_Management import TweetManagement
import CommonFunction

# 定数
IMAGE_SHOW_WIDTH = 300
IMAGE_MAX_NUM = 4

# 変数
filePaths = None
imageGrids = []

def execTweet():
	# 入力値を取得
	user_input = text_box.get("1.0", tk.END)  # "1.0" は最初の行の最初の文字を示す

	# 設定ファイルに値を保存
	configMgmt['TWITTER']['IS_TWEET'] = str(isTwitter.get())
	configMgmt['MISSKEY']['IS_TWEET'] = str(isMisskey.get())
	configMgmt['MASTODON']['IS_TWEET'] = str(isMastodon.get())
	configMgmt['BLUESKY']['IS_TWEET'] = str(isBluesky.get())
	TweetManagement.writeIniFileMgmt(configMgmt)

	# ツイートする
	if selected_tweet_type.get() == 1 :
		tweetMgmt.execTweetSingle(
			message=user_input, 
			imagePaths=filePaths if filePaths else None
		)
	elif selected_tweet_type.get() == 2 :
		tweetMgmt.execTweetReply(
			message=user_input, 
			imagePaths=filePaths if filePaths else None
		)
	elif selected_tweet_type.get() == 3 :
		tweetMgmt.execTweetQuote(
			message=user_input, 
			imagePaths=filePaths if filePaths else None
		)
	else :
		tweetMgmt.execTweetSingle(
			message=user_input, 
			imagePaths=filePaths if filePaths else None
		)

	messagebox.showinfo("終了", "終了しました")  # 取得した内容を表示するためのダイアログ

# ファイル選択ダイアログを開き、複数ファイルを選択可能に設定
def selectUploadFiles():
	# ファイル選択ダイアログを開き、複数ファイルを選択可能に設定
	global filePaths
	filePaths = filedialog.askopenfilenames(
		title="画像を選択",
		filetypes=[("画像ファイル", "*.jpg *.jpeg *.png")]
	)

	# 画像表示領域とファイルサイズを初期化
	total_size = 0
	while imageGrids:
		imageGrid = imageGrids.pop()
		imageGrid.destroy()

	# ファイルが多い、あるいは0の場合の処理
	if len(filePaths) > IMAGE_MAX_NUM:
		filePaths = None
		messagebox.showinfo("終了", "画像は" + str(IMAGE_MAX_NUM) + "枚まで指定できます")
	elif len(filePaths) > 0:
		i = 0
		for filePath in filePaths:
			# 画像サイズを取得して合計サイズに追加
			total_size += os.path.getsize(filePath)

			# 画像を読み込み、リサイズ
			image = Image.open(filePath)
			width, height = image.size
			aspect_ratio = height / width
			new_height = int(IMAGE_SHOW_WIDTH * aspect_ratio)
			image = image.resize((IMAGE_SHOW_WIDTH, new_height))
			imgTK = ImageTk.PhotoImage(image, master=frame)

			# ラベルに画像を表示
			image_label = tk.Label(frame, image=None)
			image_label.image = None
			image_label.grid(row=11+i, column=0, pady=10, padx=10, sticky="w")
			image_label.config(image=imgTK, text="")
			image_label.image = imgTK  # 参照を保持
			imageGrids.append(image_label)
			i += 1
	else:
		filePaths = None
		
	# ファイルを選択している場合、更新する
		
	# 合計サイズをMB単位に変換して表示
	total_size_mb = total_size / (1024 * 1024)
	size_label.config(text=f"合計サイズ: {total_size_mb:.2f} MB")
	
	# スクロール領域を更新
	canvas.configure(scrollregion=canvas.bbox("all"))

def update_scrollregion(event):
	canvas.configure(scrollregion=canvas.bbox("all"))

# ツイート一元管理インスタンスの作成
tweetMgmt = TweetManagement()

# メインウィンドウの作成
root = tk.Tk()
root.iconbitmap("fabicon.ico")
root.title("ツイート入力フォーム")
root.geometry("400x600")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# スクロールバーを付ける
canvas = tk.Canvas(root)
frame = tk.Frame(canvas)
scrollbar = tk.Scrollbar(
	root, orient=tk.VERTICAL, command=canvas.yview
)
canvas.configure(yscrollcommand=scrollbar.set)
frame.bind("<Configure>", update_scrollregion)  # Frameのサイズ変更イベントにスクロール領域の更新をバインド

scrollbar.grid(row=0, column=1, sticky="ns")
canvas.grid(row=0, column=0, sticky="nsew")

# Canvas上の座標(0, 0)に対してFrameの左上（nw=north-west）をあてがうように、Frameを埋め込む
canvas.create_window((0, 0), window=frame, anchor="nw")

# テキストボックスの作成（複数行の入力が可能）
text_box = tk.Text(frame, height=10, width=40)
text_box.grid(row=0, column=0, pady=10, padx=10, sticky="w")

# 画像を選択
upload_button = tk.Button(frame, text="画像を選択", command=selectUploadFiles)
upload_button.grid(row=1, column=0, pady=10, padx=10, sticky="w")

# 画像 合計サイズ表示用ラベル
size_label = tk.Label(frame, text="合計サイズ: 0.00 MB", font=("Arial", 12))
size_label.grid(row=2, column=0, pady=10, padx=10, sticky="w")

# ラジオボタンの作成
selected_tweet_type = tk.IntVar(value=1)
radio_button_1 = tk.Radiobutton(frame, text="そのままツイート", value=1, variable=selected_tweet_type)
radio_button_1.grid(row=3, column=0, sticky="w")
radio_button_2 = tk.Radiobutton(frame, text="直前のツイートにリプライする形でツイート", value=2, variable=selected_tweet_type)
radio_button_2.grid(row=4, column=0, sticky="w")
radio_button_3 = tk.Radiobutton(frame, text="直前のツイートを引用する形でツイート", value=3, variable=selected_tweet_type)
radio_button_3.grid(row=5, column=0, sticky="w")

# 設定ファイルを読み込み
configMgmt = TweetManagement.readIniFileMgmt()

# チェックボックスを作成
isTwitter = tk.IntVar(value=configMgmt['TWITTER']['IS_TWEET'])
isMisskey = tk.IntVar(value=configMgmt['MISSKEY']['IS_TWEET'])
isMastodon = tk.IntVar(value=configMgmt['MASTODON']['IS_TWEET'])
isBluesky = tk.IntVar(value=configMgmt['BLUESKY']['IS_TWEET'])

isTwitterCheck = tk.Checkbutton(frame, text="Twitterに投稿する", variable=isTwitter)
isTwitterCheck.grid(row=6, column=0, sticky="w", padx=10, pady=5)

isMisskeyCheck = tk.Checkbutton(frame, text="Misskeyに投稿する", variable=isMisskey)
isMisskeyCheck.grid(row=7, column=0, sticky="w", padx=10, pady=5)

isMastodonCheck = tk.Checkbutton(frame, text="Mastodonに投稿する", variable=isMastodon)
isMastodonCheck.grid(row=8, column=0, sticky="w", padx=10, pady=5)

isBlueskyCheck = tk.Checkbutton(frame, text="Blueskyに投稿する", variable=isBluesky)
isBlueskyCheck.grid(row=9, column=0, sticky="w", padx=10, pady=5)

# ツイート実行ボタンを作成
submit_button = tk.Button(frame, text="Tweet送信", command=execTweet)
submit_button.grid(row=10, column=0, pady=10, padx=10, sticky="w")

# ウィンドウを表示
root.mainloop()
