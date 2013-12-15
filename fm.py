#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
# Filename: DoubanFm.py

import os, io, sys
import urllib, urllib2, cookielib
import pickle, os, ConfigParser
import copy
import urlparse
import Tkinter
import bs4
import PyV8
import json
from PIL import Image, ImageTk
import db


class Douban:
	"""calss Douban
	"""
	m_site = 'http://www.douban.com'									#site
	m_loginAddr = 'http://www.douban.com/login'							#login url
	m_loveMusicListPage = 'http://douban.fm/mine'						#love music's recode page, use to get magic num(send ajax request to get music info in this page)
	m_loveMusicAjaxAddr = 'http://douban.fm/j/play_record'				#send this ajax data to get love music info
	m_subjectPage = 'http://music.douban.com/subject/%s/'				#subject page, use sid to get ssid ,which can fanily get music url
	m_musicUrlAddr = 'http://music.douban.com/j/songlist/get_song_url'  #use this url, sid and ssid to get music url 


	def __init__(self, userName, password):
		self.m_cookieJar = cookielib.LWPCookieJar()
		self.m_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.m_cookieJar))
		self.m_opener.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')]
		urllib2.install_opener(self.m_opener)
		self.m_userName = userName
		self.m_password = password
		self.m_dirToSaveSongs = os.path.normcase(os.path.join('songs/'))
		if os.path.exists(self.m_dirToSaveSongs) == False:
			os.mkdir(self.m_dirToSaveSongs)


	def Login(self):
		"""login. 

		send request with username, password and captcha. create cookie store these for service using 
		"""
		userInfo = {							
			'form_email' : self.m_userName,
			'form_password' : self.m_password,
			'captcha-solution' : '',		#the word in captcha image
			'captcha-id' : '',				#captcha id(image name)
			'referrer' : self.m_site,
			'source' : 'fm'
		}
		userInfoNoCap = {
			'form_email' : self.m_userName,
			'form_password' : self.m_password,
			'referrer' : self.m_site,
			'source' : 'fm'	
		}
		print 'login site: www.douban.com'
		print 'user  name: ' + self.m_userName
		try:
			print '...login...please wait several seconds...'
			soup = bs4.BeautifulSoup(self.m_opener.open(self.m_loginAddr).read(), from_encoding="UTF-8")
		except:
			print "error:can't connect to internet"
			return False
		checkImageNode = soup.find('img', 'captcha_image')
		if checkImageNode != None:
			tempArg = ['']
			self._PicCheck(checkImageNode['src'], tempArg)	 #pass list arg 'tempArg', which func change it will same as C's pointer
			userInfo['captcha-id'] = urlparse.parse_qsl(checkImageNode['src'])[0][1]
			userInfo['captcha-solution'] = tempArg[0]
			requestStr = urllib2.Request(self.m_loginAddr, urllib.urlencode(userInfo))
		else:
			requestStr = urllib2.Request(self.m_loginAddr, urllib.urlencode(userInfoNoCap))
		print '...login...sending request...'
		returnObj = self.m_opener.open(requestStr)
		if returnObj.geturl() == self.m_site or returnObj.geturl() == self.m_site + '/':  #return www.douban.com/ or www.douban.com
			print 'login success'
			return True
		else:
			print 'login faild'
			print 'return url is', returnObj.geturl()
			return False


	def _PicCheck(self, imageAddr, tempArg):
		"""get captcha value
		"""
		root  = Tkinter.Tk(className='input')
		
		tkImage = self._ImagesrcToTkimage(imageAddr)

		label = Tkinter.Label(root)
		label.configure(image=tkImage)
		label.pack(padx=5, pady=5)

		input = Tkinter.Entry(root)
		input.pack()
		input.focus_set()

		button = Tkinter.Button(root, text="OK", width=10, command=lambda:self._PicCheckCbFunc(root, input.get(), tempArg))
		button.pack(padx=5, pady=5)	

		root.mainloop()


	def _ImagesrcToTkimage(self, src):
		"""convert a image src to TK image obj
		"""
		imageBytes = urllib2.urlopen(src).read()
		dataStream = io.BytesIO(imageBytes)
		pilImage   = Image.open(dataStream)
		tkImage    = ImageTk.PhotoImage(pilImage)
		return tkImage


	def _PicCheckCbFunc(self, root, strValue, tempArg):
		"""button's callback func
		"""
		tempArg[0] = strValue
		root.destroy()


	def GetLoveMusicList(self):
		"""open fm's music list page and get music info, not about music url

		music info is list. and the element is dict.
		eg. [{}, {}, {}]
		"""
		AjaxInfo = {
			'ck' : '',					#str in cookie
			'spbid' : '',             	#sp(magic num) + bid(str in cookie)
			'type' : 'liked',
			'start' : '0'				#page. eg, 0, 15, 30
		}
		AjaxInfo['ck'] = [cookie.value for cookie in self.m_cookieJar if cookie.name == 'ck'][0].split('"')[-2]
		self._DebugPrint('ck=' + AjaxInfo['ck'])
		sp = self._GetRecodeListMagicNum()
		bid = [cookie.value for cookie in self.m_cookieJar if cookie.name == 'bid'][0].split('"')[-2]
		self._DebugPrint('spbid=' + sp + bid)
		AjaxInfo['spbid'] = sp + bid
		self._DebugPrint(AjaxInfo)

		musicInfo = []
		isLoop = True
		pageMusicStart = 0
		
		while isLoop == True:
			print '...request page, start at', pageMusicStart, '...'
			AjaxInfo['start'] = str(pageMusicStart) #convert int to str
			jsonOriginal = self._RequestAjaxData(self.m_opener, self.m_loveMusicAjaxAddr, AjaxInfo, 'http://douban.fm/mine')
			jsonObject = json.loads(jsonOriginal)
			pageMusicStart = pageMusicStart + jsonObject['per_page']
			if pageMusicStart >= jsonObject['total']:
				isLoop = False
			self._DebugPrint(jsonObject)

			for singleRecode in jsonObject['songs']:
				oneMusicDict = {}
				oneMusicDict['imgId'] = singleRecode['picture'].split('/')[-1]   	#pic url. i just svae last serial num
				oneMusicDict['artist'] = singleRecode['artist']						#singer
				oneMusicDict['title'] = singleRecode['title']						#music title
				oneMusicDict['subject_title'] = singleRecode['subject_title']		#album title
				oneMusicDict['subjectId'] = singleRecode['path'].split('/')[-2]		#album id
				oneMusicDict['id'] = singleRecode['id']								#sid, use this to get subject ssid in subject page, then get music url
				oneMusicDict['url'] = ''  				#this json file have no music url, we make it null for later filling
				oneMusicDict['state'] = 'NOT_DOWNLOAD' 	#NOT_DOWNLOAD, DOWNLOADED
				self._DebugPrint(oneMusicDict)
				musicInfo.append(copy.deepcopy(oneMusicDict))
				break          #for test, just get first music
			isLoop = False     #for test, just get first page music
		print 'get all music info over'
		return musicInfo


	def _RequestAjaxData(self, opener, url, data=None, referer=None):
		"""a very sample ajax data request func. read return data and decode with utf-8
		"""
		request = {}
		if data == None:
			request = urllib2.Request(url)
		else:
			request = urllib2.Request(url, urllib.urlencode(data))
		request.add_header('User-agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
		request.add_header('X-Requested-With', 'XMLHttpRequest')
		if referer:
			request.add_header('Referer', referer)
		returnObj = self.m_opener.open(request).read().decode('utf-8')
		self._DebugPrint(returnObj)
		return returnObj


	def _GetRecodeListMagicNum(self):
		"""open 'http://douban.fm/mine', find script. using PyV8 eval this script to get magic num

		in fm's love music recode page, get love music list will send ajax request, in which part of 'spbid' str is create by a piece of js code 
		"""
		pyv8Scope = _Global()  #in this page's js code, val 'window.user_id_sign' is used, so we create this inv
		ctxt = PyV8.JSContext(pyv8Scope)
		ctxt.enter()

		print '...get ajax magic code...please wait several minute...'
		listPageObj = self.m_opener.open(self.m_loveMusicListPage)
		soup = bs4.BeautifulSoup(listPageObj.read(), from_encoding='UTF-8')
		script = soup.find('div', id='play_record').find_all('script')[-1].string
		self._DebugPrint('script=' + script)
		ctxt.eval(script)

		self._DebugPrint('user_id_sign=' + pyv8Scope.window.user_id_sign)  #get 'window.user_id_sign'
		return pyv8Scope.window.user_id_sign


	def GetLoveMusicUrl(self, musicInfo, isRepeatGetUrl=False):
		"""give musicinfo list, fill it's url info

		enter subject page to get ssid, then use sid and ssid fetching music url 
		"""
		print 'get love music url start'
		sumLen = len(musicInfo)
		for idx, singleRecode in enumerate(musicInfo):   #enumerate return idx and ele
			if singleRecode['url'] != '' and singleRecode['url'] != None and isRepeatGetUrl == False:  #xml, [url] is None
				print 'music', singleRecode['title'], 'url is already exist. pass'
				continue
			print '...get music', str(idx), 'of', str(sumLen), singleRecode['title'], 'url...'
			url = self.m_subjectPage % singleRecode['subjectId']
			ssid = ''
			try:
				soup = bs4.BeautifulSoup(self.m_opener.open(url).read(), from_encoding="UTF-8")
				ssid = soup.find('li', id=singleRecode['id'])['data-ssid']   #use sid to get music ssid
				self._DebugPrint('ssid=' + ssid)
			except:
				print 'open subject page or read subject info faild, will pass this music'
				continue

			url = self.m_musicUrlAddr + '?sid=' + singleRecode['id'] + '&ssid=' + ssid   #get method. sid and ssid is requal
			try:
				jsonOriginal = self.m_opener.open(url).read().decode('utf-8')
				jsonObject = json.loads(jsonOriginal)
				singleRecode['url'] = jsonObject['r']
				self._DebugPrint(jsonObject['r'])
			except:
				print 'get music url faild, will pass this music'
				continue
		print 'get love music url over'
		return musicInfo

	def DownloadMusic(self, musicInfo, isRepeatDownload=False):
		"""give a music info list, use its url info to downlaod

		will return music info, in which music['state'] is changed
		"""
		print 'download music start'
		for music in musicInfo:
			if music['url'] == '' or music['url'] == None:
				print 'pass music', music['title'], 'which has no url. pass'
				continue
			if music['state'] == 'NOT_DOWNLOAD' or isRepeatDownload == True:
				print '...downlaoding music', music['title'], '...'
				try:
					extName = music['url'].split('.')[-1] 
					fileName = music['title'] + '_' + music['artist'] + '.' + extName
					fileName = self._SlugifyStr(fileName)
					urllib.urlretrieve(music['url'], self.m_dirToSaveSongs + fileName)
					self._DebugPrint(self.m_dirToSaveSongs + fileName)
					music['state'] = 'DOWNLOADED'
				except:
					print '...downlaod music', music['title'], 'faild...'
			else:
				print 'music', music['title'], 'has already download. pass'
		print 'download music over'
		return musicInfo

	def _SlugifyStr(self, value):
		"""replace uniqual char in str
		"""
		for s in ['|', '<', '>', '/', '\\', ':', '*', '?', '"']:
			value = value.replace(s, ' ')
		value = value.replace('&amp', '&')
		value = value.replace('&#39', "'")
		return value

	def _DebugPrint(self, str):
		"""just debug print
		"""
		#print 'debug:',
		#print str
		pass

	def _DebugWriteSoupToFile(self, fileNameStr, content):
		"""write soup string into file

		soup.prettify() to get string output.
		"""
		fileObj = file(fileNameStr, 'w+')
		fileObj.write(content.encode('utf-8'))
		fileObj.close()

class _MockWindow(object):
	"""this obj is PyV8 global obj's window obj
	"""
	def __init__(self):
		self.user_id_sign = ''

class _Global(PyV8.JSClass):
	"""this is a obj bind to PyV8's global env
	"""
	def __init__(self):
		self.window = _MockWindow()	


#func to open db file
def OpenDbFile(dbObj, fileName):
	"""open db file and read its content. if file not exist, create and read it 
	"""
	openRe = dbObj.OpenFile(fileName)
	if openRe == 1:
		if dbObj.CreateFile(fileName) != 0:
			sys.exit(1)
		else:
			dbObj.OpenFile(fileName)
	elif openRe != 0:
		sys.exit(1)


#func use db data to fill music info
def FillInfo(info, dbObj):
	for oneMusicDict in info:
		subjectId = oneMusicDict['subjectId']
		sid = oneMusicDict['id']
		for col in dbObj.m_data:
			if col['subjectId'] == subjectId and col['id'] == sid:
				oneMusicDict['url'] = col['url']		
				oneMusicDict['state'] = col['state']
				break

#func to save download state
def SaveState(dbObj, fileName, info):
	dbObj.m_data = info
	dbFileObj.SaveFile(fileName)

#main func
if __name__ == '__main__':
	fileConfig = ConfigParser.ConfigParser()
	fileConfig.read('config.ini')
	user_email = fileConfig.get('user', 'email')
	user_password = fileConfig.get('user', 'password')

	if user_email == '' or user_password == '':
		print 'user_email or password is null, please edit config.ini and fill these info!'
	else:
		doubanFM = Douban(user_email, user_password)
		if doubanFM.Login() != True:
			print 'login faild. you restart this program again.'
			sys.exit(0)
		else:
			dbFileObj = db.XmlDatabase()
			fileName = doubanFM.m_dirToSaveSongs + 'db.xml'
			OpenDbFile(dbFileObj, fileName)

			info = doubanFM.GetLoveMusicList()
			FillInfo(info, dbFileObj)  #use db file's data to fill info list: 'url' and 'if is download'

			infoWithMusicUrl = doubanFM.GetLoveMusicUrl(info)
			infoChangeState = doubanFM.DownloadMusic(infoWithMusicUrl)

			SaveState(dbFileObj, fileName, infoChangeState)
			