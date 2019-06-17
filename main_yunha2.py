#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import commands
import time
import requests
import re
import sys

from flask import Flask, jsonify, request, redirect, url_for, render_template
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch

reload(sys)
sys.setdefaultencoding('utf-8')

elasticsearch_host = "127.0.0.1"
elasticsearch_port = "9200"
es = Elasticsearch([{'host':elasticsearch_host, 'port':elasticsearch_port}], timeout=1000)

app = Flask(__name__)

url_list = [] #crawling한 url 저장
craw_list = [] #crawling된 정보 저장

def web_crawling(url, id_count):
	
	start = time.time()

	#input html에서 URL을 받아옴 
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")

	words = str(soup)
        words = re.sub('<.+?>', '', words, 0, re.I|re.S)
        words = words.lower().strip().split()

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

        #처리시간 체크
	time_check = time.time() - start

	doc = {
		"url" : url,
		"words" : words,
		"count" : count,
		"count2" : count2,
		"time" : time_check,
	}

	es.index(index="pe", doc_type="ex", id=id_count, body=doc)

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
		web_crawling(url, 1)

		res = es.get(index="pe", doc_type="ex", id=1)
		
		d = {}
		
		d['words'] = res['_source']['words']
		d['count'] = res['_source']['count']
		d['count2'] = res['_source']['count2']
		d['time'] = res['_source']['time']

		craw_list.append(d)

		#crawl 결과를 output.html로 리턴 
		return render_template('txtout.html', url_list = url_list, craw_list = craw_list)
	
@app.route('/txt_url',methods = ['POST','GET'])
def txt_url():
	if request.method == 'POST':
		#text file이름을 받아옴
		txt=request.form['textname']
		#url_list= []

		#test_txt폴더에 있는 txt파일들중 이름이 같은 파일을 찾아서 파일을 연다
		f = open("./test_txt/"+txt+".txt",'r')
		#거기에 있는 URL을 list로 받음
		id_count = 1
		while True:
			line = f.readline()
			if not line: break
			
			url_list.append(line)
			id_count = id_count + 1	
			web_crawling(line, id_count)

			res = es.get(index="pe", doc_type="ex", id=id_count)

               		d = {}

                	d['words'] = res['_source']['words']
                	d['count'] = res['_source']['count']
                	d['count2'] = res['_source']['count2']
                	d['time'] = res['_source']['time']
					
			craw_list.append(d)
		
		f.close()
		#url리스트들을 txtout.html로 넘김
		return render_template('txtout.html', url_list = url_list, craw_list = craw_list)



if __name__ == '__main__':
    	try:
		#저장된 문서 개수
		#id_count = 0
        	parser = argparse.ArgumentParser(description="")
        	parser.add_argument('--listen-port',  type=str, required=True, help='REST service listen port')
        	args = parser.parse_args()
        	listen_port = args.listen_port
    	except Exception, e:
        	print('Error: %s' % str(e))
	ipaddr=commands.getoutput("hostname -I").split()[0]
	print "Starting the service with ip_addr="+ipaddr
	app.run(debug=False,host=ipaddr,port=int(listen_port))

