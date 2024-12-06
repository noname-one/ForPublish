# パッケージの読み込み
import datetime
import requests
import configparser
import os
from bs4 import BeautifulSoup
#-------------------------------------------------------------------

# 今日の日付取得
def getToday():
	today = datetime.date.today()
	return today.strftime('%Y-%m-%d')

# UNIX時間を日本標準時に変換する
def getJSTFromUnix(time):
	dt = datetime.datetime.fromtimestamp(time)
	return dt.strftime('%Y-%m-%d %H:%M:%S')

# ファイル取得
def getFileContent(fileFullName):
	f = open(fileFullName, encoding='UTF-8')
	ret = f.read()
	f.close()
	
	return ret

# ファイル書き換え
def updFileContent(fileFullName, content, chara='UTF-8'):
	f = open(fileFullName, 'w', encoding=chara)
	f.write(str(content))
	f.close()

# htmlから最初のimg画像を取得
def getFirstImg(html):
	soup = BeautifulSoup(html,'lxml')
	imgs = soup.findAll('img')
	
	for img in imgs:
		if img.get('src').find('inoreader') == -1:
			return img.get('src');
	
	return ''
	
# ページをhtmlとして取得
def getHTML(url):
	ret = ''
	try:
		# コールアウトに必要な情報を格納
		res = requests.get(url)
		ret = res.text
	except:
		CommonFunction.updFileContent(trgtFolder + "エラー.txt", "ステータスコード:" + str(res.status_code) + " ステータス詳細:" + str(res.text))
		return ''
	return ret

# Iniファイル読み込み関連-------------------------------------------------------------------
def readIniFile(ini_path, configFileName):
	# 設定ファイルのパスを設定
	ini_base_path = os.path.join(ini_path, configFileName)

	# iniファイルが存在するか確認
	if not os.path.exists(ini_base_path):
		raise FileNotFoundError(f"{ini_base_path} が見つかりません。")

	# 設定ファイルから認証情報を読み込む
	config = configparser.ConfigParser(interpolation=None)
	config.read(ini_base_path, encoding='utf-8')
	return config

def writeIniFile(afterConfig, ini_path, configFileName):
	# 設定ファイルのパスを設定
	ini_base_path = os.path.join(ini_path, configFileName)

	# ファイルへ保存
	with open(ini_base_path, "w", encoding="utf-8") as configfile:
		afterConfig.write(configfile)