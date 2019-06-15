#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import commands
from flask import Flask, jsonify, request, redirect, url_for, render_template

import requests
from bs4 import BeautifulSoup
import re
import sys

app = Flask(__name__)

@app.route('/')
def main():
	# input  html을 리턴 
	return render_template('input.html')

@app.route('/crawl_url', methods = ['POST', 'GET'])
def crawl_url():
	if request.method == 'POST':
		
		#input html에서 URL을 받아옴 
		url = request.form['URL']
		res = requests.get(url)
		soup = BeautifulSoup(res.content, "html.parser")
		
		words = str(soup)
		words = re.sub('<.+?>', '', words, 0, re.I|re.S)		
		words = words.lower().strip().split()
		
		#전체 단어수 세기 
		count = 0
		 
		#처리시간 체크 
		time = 0
	
	#crawl 결과를 output.html로 리턴 
	return render_template('output.html', url = url, count = count, time = time)	

	

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

