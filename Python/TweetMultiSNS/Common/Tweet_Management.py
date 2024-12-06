# パッケージの読み込み
import tweepy
from misskey import Misskey
from mastodon import Mastodon
from atproto import Client as Bluesky, client_utils as BlueskyUtils
from datetime import datetime, date, timedelta
from tkinter import messagebox
import webbrowser
import re
import configparser
import traceback
import os
import requests
from bs4 import BeautifulSoup
from enum import Enum

# 独自パッケージの読み込み
import sys
if getattr(sys, 'frozen', False):
	# PyInstallerでバンドルされた実行ファイルの場合
	base_path = sys._MEIPASS
else:
	# スクリプトを直接実行している場合
	base_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(base_path)
import CommonFunction

class TweetManagement:
	#-----定数--------------------------------------------------------------
	MAX_NUM_ATTACH_IMAGES = 4
	CONFIG_FILE_NAME_MGMT = 'Tweet_Management.ini'
	CONFIG_FILE_NAME_AUTH = 'Tweet_AuthInfo.ini'
	TWEET_TYPE = Enum('TWEET_TYPE', ['SINGLE', 'REPLY', 'QUOTE'])

	#-----コンストラクタ--------------------------------------------------------------
	def __init__(self):
		try:
			# メンバ変数の初期化
			self.twitterClient = None
			self.misskeyClient = None
			self.mastodonClient = None
			self.blueskyClient = None
			self.twitterParentTweetId = ''
			self.misskeyParentTweetId = ''
			self.mastodonParentTweetId = ''
			self.blueskyRootTweet = None
			self.blueskyParentTweet = None
			self.errMsg = []
		except:
			self.addErrMsg('---------------------全般エラー---------------------\n' + traceback.format_exc())

	#-----ツイート関連のメソッド--------------------------------------------------------------
	# Twitter 接続インスタンスを作成
	def CreateTwitterInstance(self):
		try:
			twitter_config = self.configAuth['TWITTER']
			if self.twitterClient == None and self.configMgmt['TWITTER']['IS_TWEET'] == '1':
				self.twitterClient = tweepy.Client(
					bearer_token = twitter_config['BEARER_TOKEN'],
					consumer_key = twitter_config['API_KEY'],
					consumer_secret = twitter_config['API_SECRET'],
					access_token = twitter_config['ACCESS_TOKEN'],
					access_token_secret = twitter_config['ACCESS_TOKEN_SECRET']
				)
		except:
			self.addErrMsg('---------------------Twitter認証エラー---------------------\n' + traceback.format_exc())

	# Misskey 接続インスタンスを作成
	def CreateMisskeyInstance(self):
		try:
			misskey_config = self.configAuth['MISSKEY']
			if self.misskeyClient == None and self.configMgmt['MISSKEY']['IS_TWEET'] == '1':
				self.misskeyClient = Misskey(misskey_config['SERVER_NAME'], i=misskey_config['ACCESS_TOKEN'])
		except:
			self.addErrMsg('---------------------Misskey認証エラー---------------------\n' + traceback.format_exc())

	# Mastodon 接続インスタンスを作成
	def CreateMastodonInstance(self):
		try:
			mastodon_config = self.configAuth['MASTODON']
			if self.mastodonClient == None and self.configMgmt['MASTODON']['IS_TWEET'] == '1':
				self.mastodonClient = Mastodon(
					api_base_url = mastodon_config['SERVER_URL'],
					client_id = mastodon_config['CLIENT_ID'],
					client_secret = mastodon_config['CLIENT_SECRET'],
					access_token = mastodon_config['ACCESS_TOKEN']
				)
		except:
			self.addErrMsg('---------------------Mastodon認証エラー---------------------\n' + traceback.format_exc())

	# Bluesky 接続インスタンスを作成
	def CreateBlueskyInstance(self):
		try:
			bluesky_config = self.configAuth['BLUESKY']
			if self.blueskyClient == None and self.configMgmt['BLUESKY']['IS_TWEET'] == '1':
				self.blueskyClient = Bluesky()
				self.blueskyClient.login(bluesky_config['LOGIN_ID'], bluesky_config['LOGIN_PW'])
		except:
			self.addErrMsg('---------------------Bluesky認証エラー---------------------\n' + traceback.format_exc())

	# Twitter ツイート実行
	def CreateTwitterTweet(self, message, tweetType, imagePaths=None):
		try:
			if self.configMgmt['TWITTER']['IS_TWEET'] == '1':
				tweet = None
				media_ids = []

				# 画像がある場合、アップロードしてメディアIDを取得
				if imagePaths:
					# v1.1 APIクライアントのセットアップ（OAuth1UserHandlerを使用）
					twitter_config = self.configAuth['TWITTER']
					auth = tweepy.OAuth1UserHandler(
						consumer_key=twitter_config['API_KEY'],
						consumer_secret=twitter_config['API_SECRET'],
						access_token=twitter_config['ACCESS_TOKEN'],
						access_token_secret=twitter_config['ACCESS_TOKEN_SECRET']
					)
					v1_client = tweepy.API(auth)
					# 画像を一枚ずつアップロード
					for imagePath in imagePaths:
						try:
							media_response = v1_client.media_upload(imagePath)
							media_ids.append(media_response.media_id)
						except:
							self.addErrMsg(f"Twitter 画像のアップロード中にエラーが発生しました: {imagePath}\n" + traceback.format_exc())

				# ツイートの種類に応じて投稿
				if self.twitterParentTweetId != '':
					match tweetType:
						case TweetManagement.TWEET_TYPE.SINGLE:
							tweet = self.twitterClient.create_tweet(
								text=message,
								media_ids=media_ids if media_ids else None
							)
						case TweetManagement.TWEET_TYPE.REPLY:
							tweet = self.twitterClient.create_tweet(
								text=message, 
								in_reply_to_tweet_id=self.twitterParentTweetId,
								media_ids=media_ids if media_ids else None
							)
						case TweetManagement.TWEET_TYPE.QUOTE:
							tweet = self.twitterClient.create_tweet(
								text=message, 
								quote_tweet_id=self.twitterParentTweetId,
								media_ids=media_ids if media_ids else None
							)
						case _:
							tweet = self.twitterClient.create_tweet(
								text=message,
								media_ids=media_ids if media_ids else None
							)
				else:
					tweet = self.twitterClient.create_tweet(
						text=message,
						media_ids=media_ids if media_ids else None
					)

				# ツイートのIDを保持
				if tweet:
					self.twitterParentTweetId = tweet.data['id']
		except:
			self.addErrMsg('---------------------Twitter実行エラー---------------------\n' + traceback.format_exc())

	# Misskey ツイート実行
	def CreateMisskeyTweet(self, message, tweetType, imagePaths=None):
		try:
			if self.configMgmt['MISSKEY']['IS_TWEET'] == '1':
				misskeyRet = None
				media_ids = []

				# 画像がある場合、アップロードしてfile_idsを取得
				if imagePaths:
					for imagePath in imagePaths:
						try:
							upload_response = self.misskeyClient.drive_files_create(file=open(imagePath, 'rb'))
							media_ids.append(upload_response['id'])
						except:
							self.addErrMsg(f"Misskey 画像のアップロード中にエラーが発生しました: {imagePath}\n" + traceback.format_exc())

				if self.misskeyParentTweetId != '':
					match tweetType:
						case TweetManagement.TWEET_TYPE.SINGLE:
							misskeyRet = self.misskeyClient.notes_create(
								text=message,
								file_ids=media_ids if media_ids else None
							)
						case TweetManagement.TWEET_TYPE.REPLY:
							misskeyRet = self.misskeyClient.notes_create(
								text=message, 
								reply_id=self.misskeyParentTweetId,
								file_ids=media_ids if media_ids else None
							)
						case TweetManagement.TWEET_TYPE.QUOTE:
							misskeyRet = self.misskeyClient.notes_create(
								text=message, 
								renote_id=self.misskeyParentTweetId,
								file_ids=media_ids if media_ids else None
							)
						case _:
							misskeyRet = self.misskeyClient.notes_create(
								text=message,
								file_ids=media_ids if media_ids else None
							)
				else:
					misskeyRet = self.misskeyClient.notes_create(
						text=message,
						file_ids=media_ids if media_ids else None
					)

				# ツイートのIDを保持
				if misskeyRet:
					self.misskeyParentTweetId = misskeyRet['createdNote']['id']
		except:
			self.addErrMsg('---------------------Misskey実行エラー---------------------\n' + traceback.format_exc())

	# Mastodon ツイート実行
	def CreateMastodonTweet(self, message, tweetType, imagePaths=None):
		try:
			if self.configMgmt['MASTODON']['IS_TWEET'] == '1':
				mastodonRet = None
				media_ids = []

				# 画像がある場合、アップロードしてmedia_idsを取得
				content_type = ""
				if imagePaths:
					for imagePath in imagePaths:
						try:
							# ファイル拡張子に応じたContent-Typeを設定
							extension = imagePath.split(".")[-1].lower()
							if extension in ["jpg", "jpeg"]:
								content_type = "image/jpeg"
							elif extension == "png":
								content_type = "image/png"
							else:
								self.addErrMsg(f"未対応の画像形式: {imagePath}")
								continue
							# 画像をアップロード
							with open(imagePath, 'rb') as file:
								media_response = self.mastodonClient.media_post(media_file=file, mime_type=content_type)
								media_ids.append(media_response['id'])
						except:
							self.addErrMsg(f"Mastodon 画像のアップロード中にエラーが発生しました: {imagePath}\n" + traceback.format_exc())

				if self.mastodonParentTweetId != '':
					match tweetType:
						case TweetManagement.TWEET_TYPE.SINGLE:
							mastodonRet = self.mastodonClient.status_post(
								message,
								media_ids=media_ids if media_ids else None
							)
						case TweetManagement.TWEET_TYPE.REPLY:
							mastodonRet = self.mastodonClient.status_post(
								message, 
								in_reply_to_id=self.mastodonParentTweetId,
								media_ids=media_ids if media_ids else None
							)
						case TweetManagement.TWEET_TYPE.QUOTE:
							# Mastodonは引用ツイートができないため、リプライする（一部のインスタンスのみで使用可能）
							mastodonRet = self.mastodonClient.status_post(
								message, 
								in_reply_to_id=self.mastodonParentTweetId,
								media_ids=media_ids if media_ids else None
							)
						case _:
							mastodonRet = self.mastodonClient.status_post(
								message,
								media_ids=media_ids if media_ids else None
							)
				else:
					mastodonRet = self.mastodonClient.status_post(
						message,
						media_ids=media_ids if media_ids else None
					)

				# ツイートのIDを保持
				if mastodonRet:
					self.mastodonParentTweetId = mastodonRet['id']
		except:
			self.addErrMsg('---------------------Mastodon実行エラー---------------------\n' + traceback.format_exc())

	# Bluesky ツイート実行
	def CreateBlueskyTweet(self, message, tweetType, imagePaths=None):
		try:
			if self.configMgmt['BLUESKY']['IS_TWEET'] == '1':
				# 画像アップロード処理(Blob)
				images = []
				content_type = ""
				if imagePaths:
					for imagePath in imagePaths:
						try:
							# ファイル拡張子に応じたContent-Typeを設定
							extension = imagePath.split(".")[-1].lower()
							if extension in ["jpg", "jpeg"]:
								content_type = "image/jpeg"
							elif extension == "png":
								content_type = "image/png"
							else:
								self.addErrMsg(f"未対応の画像形式: {imagePath}")
								continue
							with open(imagePath, "rb") as img_file:
								blob_response = self.blueskyClient.upload_blob(img_file)
								blob = blob_response["blob"]  # 正しいBlobRefを取得
								images.append({"image": blob, "alt": ""})
						except:
							self.addErrMsg(f"Bluesky 画像のアップロード中にエラーが発生しました: {imagePath}\n" + traceback.format_exc())

				# Embed設定
				embed = None

        		# 画像がある場合は画像のembedを優先
				links = re.findall(r'https?://[^\s]+', message)
				if images:
					embed = {"$type": "app.bsky.embed.images", "images": images}
				elif links:
					external_link = links[0]  # 最初のリンクを使用
					ogp_data = self.fetch_ogp_metadata(external_link)
					thumb_blob = None
					if ogp_data['image']:
						try:
							response = requests.get(ogp_data['image'], stream=True)
							response.raise_for_status()
							thumb_blob_response = self.blueskyClient.upload_blob(response.raw)
							thumb_blob = thumb_blob_response["blob"]
						except Exception as e:
							self.addErrMsg(f"OGPサムネイル画像のアップロード中にエラーが発生しました: {e}")

					embed = {
						"$type": "app.bsky.embed.external",
						"external": {
							"uri": external_link,
							"title": ogp_data['title'],
							"description": ogp_data['description'],
							"thumb": thumb_blob  # サムネイル画像のBlobRef
						}
					}

				# 送信用のメッセージ作成
				text_builder = BlueskyUtils.TextBuilder()
				messageArray = re.split(r'(https?://[^\s]+|#[^\s]+)', message)	# 正規表現を使って「#」と「https://」で文字列を区切る
				for msg in messageArray:
					if msg.startswith("#"):
						text_builder.tag(msg, msg.lstrip("#"))
					elif msg.startswith("https://") or msg.startswith("http://"):
						text_builder.link(msg, msg)
					else:
						text_builder.text(msg)

				# ツイート実行
				blueskyRet = None
				if self.blueskyParentTweet != None:
					match tweetType:
						case TweetManagement.TWEET_TYPE.SINGLE:
							blueskyRet = self.blueskyClient.send_post(
								text=text_builder, 
								embed=embed
							)
						case TweetManagement.TWEET_TYPE.REPLY:
							blueskyRet = self.blueskyClient.send_post(
								text=text_builder,
								reply_to={
									"parent": {
										"uri": self.blueskyParentTweet["uri"],
										"cid": self.blueskyParentTweet["cid"]
									},
									"root": {
										"uri": self.blueskyRootTweet["uri"],
										"cid": self.blueskyRootTweet["cid"]
									}
								}, 
								embed=embed
							)
						case TweetManagement.TWEET_TYPE.QUOTE:
							# blueskyは引用ツイートができないため、リプライする
							blueskyRet = self.blueskyClient.send_post(
								text=text_builder,
								reply_to={
									"parent": {
										"uri": self.blueskyParentTweet["uri"],
										"cid": self.blueskyParentTweet["cid"]
									},
									"root": {
										"uri": self.blueskyRootTweet["uri"],
										"cid": self.blueskyRootTweet["cid"]
									}
								}, 
								embed=embed
							)
						case _:
							blueskyRet = self.blueskyClient.send_post(
								text=text_builder, 
								embed=embed
							)
				else:
					blueskyRet = self.blueskyClient.send_post(
						text=text_builder, 
						embed=embed
					)
					if blueskyRet:
						self.blueskyRootTweet = blueskyRet
				# ツイートのIDを保持
				if blueskyRet:
					self.blueskyParentTweet = blueskyRet
		except:
			self.addErrMsg('---------------------Bluesky実行エラー---------------------\n' + traceback.format_exc())


	#-----ツイート関連のメソッド--------------------------------------------------------------
	def execTweet(self, message, tweetType, imagePaths=None):
		try:
			# 設定ファイルを読み込み
			self.configMgmt = self.readIniFileMgmt()
			self.configAuth = self.readIniFileAuth()

			# 各SNSの認証を行う（認証済の場合スキップされる）
			self.CreateTwitterInstance()
			self.CreateMisskeyInstance()
			self.CreateMastodonInstance()
			self.CreateBlueskyInstance()

			# 設定ファイルを読み込み
			self.CreateTwitterTweet(message, tweetType, imagePaths)
			self.CreateMisskeyTweet(message, tweetType, imagePaths)
			self.CreateMastodonTweet(message, tweetType, imagePaths)
			self.CreateBlueskyTweet(message, tweetType, imagePaths)
		except:
			self.addErrMsg('---------------------想定外のエラー---------------------\n' + traceback.format_exc())
		finally:
			self.showErrMsg()

	def execTweetSingle(self, message, imagePaths=None):
		self.execTweet(
			message, 
			TweetManagement.TWEET_TYPE.SINGLE,
			imagePaths
		)

	def execTweetReply(self, message, imagePaths=None):
		self.execTweet(
			message, 
			TweetManagement.TWEET_TYPE.REPLY,
			imagePaths
		)

	def execTweetQuote(self, message, imagePaths=None):
		self.execTweet(
			message,
			TweetManagement.TWEET_TYPE.QUOTE,
			imagePaths
		)

	#-----その他のメソッド--------------------------------------------------------------
	def addErrMsg(self, message):
		self.errMsg.append(message)
	
	def showErrMsg(self):
		if len(self.errMsg) > 0:
			messagebox.showinfo("エラー", "\n".join(self.errMsg))
			print("\n".join(self.errMsg))
			self.errMsg = []

	def fetch_ogp_metadata(self, url):
		# 指定したURLのOGPメタデータを取得
		try:
			response = requests.get(url, timeout=10)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, 'html.parser')
			og_title = soup.find('meta', property='og:title')
			og_description = soup.find('meta', property='og:description')
			og_image = soup.find('meta', property='og:image')

			return {
				"title": og_title['content'] if og_title else "",
				"description": og_description['content'] if og_description else "",
				"image": og_image['content'] if og_image else None
			}
		except Exception as e:
			self.addErrMsg(f"OGP情報の取得中にエラーが発生しました: {e}")
			return {"title": "取得失敗", "description": "取得失敗", "image": None}

	#-----設定ファイル関連のメソッド--------------------------------------------------------------
	@staticmethod
	def readIniFileMgmt():
		# 設定ファイルのパスを設定
		if getattr(sys, 'frozen', False):
			# PyInstallerでバンドルされた実行ファイルの場合
			ini_base_path = os.path.dirname(sys.executable)  # 実行ファイルの場所を取得
		else:
			# スクリプトを直接実行している場合
			ini_base_path = os.path.dirname(os.path.abspath(__file__))

		# 設定ファイルを読み込み
		return CommonFunction.readIniFile(ini_base_path, TweetManagement.CONFIG_FILE_NAME_MGMT)

	@staticmethod
	def readIniFileAuth():
		# 設定ファイルのパスを設定
		if getattr(sys, 'frozen', False):
			# PyInstallerでバンドルされた実行ファイルの場合
			ini_base_path = os.path.dirname(sys.executable)  # 実行ファイルの場所を取得
		else:
			# スクリプトを直接実行している場合
			ini_base_path = os.path.dirname(os.path.abspath(__file__))

		# 設定ファイルを読み込み
		return CommonFunction.readIniFile(ini_base_path, TweetManagement.CONFIG_FILE_NAME_AUTH)

	@staticmethod
	def writeIniFileMgmt(config):
		# 設定ファイルのパスを設定
		if getattr(sys, 'frozen', False):
			# PyInstallerでバンドルされた実行ファイルの場合
			ini_base_path = os.path.dirname(sys.executable)  # 実行ファイルの場所を取得
		else:
			# スクリプトを直接実行している場合
			ini_base_path = os.path.dirname(os.path.abspath(__file__))

		# 設定ファイルを読み込み
		return CommonFunction.writeIniFile(config, ini_base_path, TweetManagement.CONFIG_FILE_NAME_MGMT)