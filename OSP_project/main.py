#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import commands
from flask import Flask, jsonify, request, redirect, url_for, render_template

import requests
from bs4 import BeautifulSoup
import re
import sys
from nltk.corpus import stopwords
from numpy import dot
from numpy.linalg import norm
import numpy 
from nltk import word_tokenize

import time
import math

app = Flask(__name__)

craw_list = []
url_list = []
doc_list = []
tf_list = []
idf_dic = {}


def tF(wor,total_word):
	
	tf_dic={}

	# 정수 뒤에 예를 들어 20.0 이렇게 되있어야 소수점 뒤까지 나옴. 그래서 .0 추가하는 부분
	total_word = float(str(total_word)+".0")

	swlist = []
	list2 = []
        bow = set()
	wordcount_d = {}

	for sw in stopwords.words("english"):
		swlist.append(sw)
	for w in wor:
		if w not in swlist:
			list2.append(w)	
	

	for tok in list2:
		if tok not in wordcount_d.keys():
			wordcount_d[tok] = 0
		wordcount_d[tok] += 1
	
		bow.add(tok)
	
	for word in bow:
		tf_dic[word] = "%0.6f" % (float)((wordcount_d[word])/(total_word))

	#for word in dic:
	#	tf_dic[word] = "%0.6f" % (float)((dic[word])/(total_word))
	
	return tf_dic

def idf():
	idf_dic = {}
	
	#전체 문서수 (elasticsearch 완성되면 바꾸기) 
	total_docu = len(url_list)
	total_docu = float(str(total_docu)+".0")
	
	swlist = []
	doc_list2 = []
	bow = set()

        for sw in stopwords.words("english"):
                swlist.append(sw)
	for i in range(0, len(doc_list), 1):
        	for w in doc_list[i]:
                	if w not in swlist:
                        	doc_list2.append(w)	
	
	for tok in doc_list2:
		bow.add(tok)	

	for word in bow: #bow은 모든  문서의 단어 정보 , word는 그중에서 단어  
		cnt = 0
		for s in doc_list: #문서 마다
			if word in s:
				cnt += 1
		idf_dic[word] = "%0.6f" % (math.log10(total_docu / cnt))
		#idf_dic[word] = cnt
	return idf_dic	
		
def tfidf(dic):
	
	idf_dic = dic

	tfidf_d = {}
	tfidf_list = []
	
	swlist = []
        doc_list2 = []
        bow = set()

        for sw in stopwords.words("english"):
                swlist.append(sw)
        for i in range(0, len(doc_list), 1):
                for w in doc_list[i]:
                        if w not in swlist:
                                doc_list2.append(w)

        for tok in doc_list2:
                bow.add(tok)
	
	
	for i in range(0, len(url_list)):
			
		#for word in tf_list[i].keys():
		#	if word in idf_dic.keys(): #여기에 못들어 가는듯 
		#		tfidf_d[word] = "%0.6f" % (float(idf_dic[word]) * float(tf_list[i][word]))
			
		for word in bow:
			if (word in tf_list[i].keys()) and (word in idf_dic.keys()):
				tfidf_d[word] = "%0.6f" % (float(idf_dic[word]) * float(tf_list[i][word]))
			else:
				tfidf_d[word] = 0
		tfidf_list.append(tfidf_d)
		tfidf_d = {}	
	return tfidf_list


def web_crawling(url):
	
	start = time.time()

	dic = {}
	#input html에서 URL을 받아옴
        #url = request.form['URL']
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")	
	words = str(soup)
        words = re.sub('<.+?>', '', words, 0, re.I|re.S)
	words = words.replace("\n"," ").replace("(","").replace(")","").replace("!","").replace('"','').replace("'",'').replace("?",'').replace("-",'').replace(".",'').replace("\t"," ").replace(":","").replace(",","").replace(";","").replace("/","")
        words = words.lower().strip().split()
	
	doc_list.append(words)
	
        #전체 단어수 세기(중복 포함) 
        count = len(words)
	#단어 수 세기(중복 미포함)
	d = {} 
	for word in words:
		if word in d:
			d[word] += 1
		else:
			d[word] = 1	

	count2 = len(d)
	
	#tf_list.append(tF(d,count))
	tf_list.append(tF(words, count))	

        #처리시간 체크
	time_check = time.time() - start

	dic = { "words" : d , "count" : count , "count2" : count2 , "time" : time_check }
	return dic


@app.route('/')
def main():
	# input  html을 리턴 
	return render_template('input.html')

@app.route('/crawl_url', methods = ['POST', 'GET'])
def crawl_url():
	if request.method == 'POST':
		url = request.form['URL']
		#input html에서 URL을 받아옴 
		url_list.append(url)	
	
		crw = web_crawling(url)
		craw_list.append(crw)
		
		idf_dic = idf()
		
		tfidf_list = []
                tfidf_list = tfidf(idf_dic)
				
		#crawl 결과를 output.html로 리턴 
		return render_template('tf.html', tf_list =tf_list , crw=crw, idf_list = idf_list, tfidf_list = tfidf_list)
		#return render_template('txtout.html', url_list = url_list, craw_list = craw_list, tf_list= tf_list)

@app.route('/txt_url',methods = ['POST','GET'])
def txt_url():
	if request.method == 'POST':
		#text file이름을 받아옴
		txt=request.form['textname']
		#url_list= []

		#test_txt폴더에 있는 txt파일들중 이름이 같은 파일을 찾아서 파일을 연다
		f = open("./test_txt/"+txt+".txt",'r')
		#거기에 있는 URL을 list로 받음
		while True:
			line = f.readline()
			if not line: break

			url_list.append(line)

			crw = web_crawling(line)						
			craw_list.append(crw)
		
		f.close()

		#for a in craw_list:	
		#	idf_list.append(idf(a["words"]))
		idf_dic = idf()			
		
		tfidf_list = []
		
		tfidf_list = tfidf(idf_dic)					

		#url리스트들을 txtout.html로 넘김
		#return render_template('txtout.html', url_list = url_list, craw_list = craw_list)
		return render_template('tf.html', tf_list=tf_list, crw=crw, idf_dic = idf_dic, tfidf_list=tfidf_list)


if __name__ == '__main__':
    	try:
        	parser = argparse.ArgumentParser(description="")
        	parser.add_argument('--listen-port',  type=str, required=True, help='REST service listen port')
        	args = parser.parse_args()
        	listen_port = args.listen_port
    	except Exception, e:
        	print('Error: %s' % str(e))
	ipaddr=commands.getoutput("hostname -I").split()[0]
	print "Starting the service with ip_addr="+ipaddr
	app.run(debug=False,host=ipaddr,port=int(listen_port))

