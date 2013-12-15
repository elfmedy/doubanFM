#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8

import os.path
import copy
import codecs
from xml.etree import ElementTree
from xml.dom import minidom

class FileDatabase:
	"""this is the paraent database class
	"""
	def __init__(self):
		self.m_data = []

	def CreateFile(self, nameStr):
		self._CoverImpError()

	def RemoveFile(self, nameStr):
		self._CoverImpError()

	def OpenFile(self, nameStr):
		self._CoverImpError()

	def CloseFile(self, nameStr):
		self._CoverImpError()

	def _CheckKey(self, key):
		if not self.m_data:
			return False
		if self.m_data[0].has_key(key):
			return True

	def SelectOne(self, cbFunc):
		"""cbFunc(data). data is a col of database, dict, you can't change the data
		"""
		for col in self.m_data:
			if cbFunc(col):
				return copy.deepcopy(col)

	def SelectMul(self, cbFunc):
		"""same as self.SelectOne, but can select many
		"""
		re = []
		for col in self.m_data:
			if cbFunc(col):
				tempCol = copy.deepcopy(col)
				re.append(tempCol)
		return re

	def UpdateOne(self, cbFunc):
		""" cbFunc(data) get a col of data(list), can check and edit. if change, return True, else False
		"""
		for col in self.m_data:
			if cbFunc(col):
				return

	def UpdateMul(self, cbFunc):
		"""same as UpdataOne, but can edit many
		"""
		for col in self.m_data:
			cbFunc(col)

	def DeleteOne(self, cbFunc):
		for col in self.m_data:
			if cbFunc(col):
				self.m_data.remove(col)
				return

	def DeleteAll(self, cbFunc):
		for col in self.m_data:
			if cbFunc(col):
				self.m_data.remove(col)

	def Insert(self, data):
		tempCol = copy.deepcopy(data)
		self.m_data.insert(tempCol)

	def _CoverImpError(self):
		raise Exception('this is a visual func which must be cover implement') 

class XmlDatabase(FileDatabase):
	"""inherit from FileDatabase
	"""
	def __init__(self):
		FileDatabase.__init__(self)
		self._m_document = {}

	def CreateFile(self, nameStr):
		if os.path.exists(nameStr):
			print "can't create file. file is exist"
			return 1
		fo = open(nameStr, 'w+')
		fo.close()
		return 0

	def RemoveFile(self, nameStr):
		if os.path.exists(nameStr):
			os.remove(nameStr)
			return 0
		else:
			print "can't remove file. file is not exist"
			return 1

	def OpenFile(self, nameStr):
		if not os.path.exists(nameStr):
			return 1
		try:
			document = ElementTree.parse(nameStr)
			root = document.getroot()
			if root != None:
				for col in root:
					colDict = {}
					for ele in col:
						colDict[ele.tag] = ele.text
					self.m_data.append(colDict)
			print 'read file success'
		except:
			print 'parse file faild. probably file is empty'
			self.m_data = []
		return 0

	def SaveFile(self, fileName):
		data = ElementTree.Element('data')
		for col in self.m_data:
			column = ElementTree.SubElement(data, 'column')
			for (key, val) in col.items():
				ele = ElementTree.SubElement(column, key)
				ele.text = val
		roughStr = ElementTree.tostring(data, 'UTF-8')
		Checkstr = minidom.parseString(roughStr).toprettyxml(indent="    ")
		#open a file with utf-8 codec(write str is utf-8 encode).
		#don't use sys open, it's default codec is ascii, probably encounter some errors
		fo = codecs.open(fileName, encoding='utf-8', mode='w+')     
		fo.write(Checkstr)
		fo.close()


if __name__ == '__main__':
	print 'this is a module for sample xml data resore'
	print 'below just a test. i create a db file "db.xml"'
	a = XmlDatabase()
	a.OpenFile('db.xml')
	a.SaveFile()
