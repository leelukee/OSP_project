#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import commands
import requests
import re
import sys
import numpy
import time
import math

from flask import Flask, jsonify, request, redirect, url_for, render_template
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from numpy import dot
from numpy.linalg import norm
from nltk import word_tokenize
from elasticsearch import Elasticsearch

reload(sys)
sys.setdefaultencoding('utf-8')

#elasticsearch 설정
elasticsearch_host = "127.0.0.1"
elasticsearch_port = "9200"
es = Elasticsearch([{'host':elasticsearch_host, 'port':elasticsearch_port}], timeout=1000)

app = Flask(__name__)

id_count = 0 #DB에 저장된 문서의 개수

craw_list = [] #crawling된 정보 저장
url_list = []

doc_list = [] #전체 단어를 저장

vector_list = []
vector_dic = {} #'url' : 'vector list' 이런 형식의 딕셔너리가 vecotr_list에 저장
cosine_s = {} #각 url마다 다른 url에 대한 유사도가 딕셔너리로 저장

tf_list = []
idf_dic = {}

def make_vector(url, words):

        doc_list2 = []
        d = {}
        v = []
        swlist = []
        bow = set()

        #stopwords list
        for sw in stopwords.words("english"):
                swlist.append(sw)

        #stopwords 제거
        for i in range(0, len(doc_list), 1):
                for w in doc_list[i]:
                        if w not in swlist:
                                doc_list2.append(w)

        for tok in doc_list2:
                bow.add(tok)

        for w in bow:
                val = 0
                for t in words:
                        if t == w:
                                val+=1

                v.append(val)

        d[url] = v


        return d #딕셔너리 리턴('url' : 'vetor array')

def cosine():
        for i in range(0, len(doc_list), 1):
                d = {}

                #url = "".join(vector_list[i].keys()) #list를 문자열로 바꿔줌
                url = url_list[i]
                a1 = []
                a1 = vector_list[i].values()[0]
                #a1 = numpy.array(vector_dic[url])

                for j in range(0, len(doc_list), 1):
                        url2 = url_list[j]
                        a2 = []
                        #a2 = numpy.array(vector_dic[url2])

                        if i != j:
                                #url2 = "".join(vector_list[j].keys())
                                a2 = vector_list[j].values()[0]
                                d[url2] = dot(a1,a2) / (norm(a1) * norm(a2))
                cosine_s[url] = d

def tF(wor, total_word):
        #wor이 아니라 전체 단어(doc_list)를 써야하는거 아닌가?
        tf_dic={}
        #print len(doc_list)
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

        return tf_dic


def idf():
        idf_dic = {}

        #전체 문서수
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

        #input html에서 URL을 받아옴
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")
        words = str(soup)
        words = re.sub('<.+?>', '', words, 0, re.I|re.S)
        words = words.replace("\n"," ").replace("(","").replace(")","").replace("!","").replace('"','').replace("'",'').replace("?",'').replace("-",'').replace(".",'').replace("\t"," ").replace(":","").replace(",","").replace(";","").replace("/","")
        words = words.lower().strip().split()

        #여기서 전체 단어 저장(문서 별로 list로)
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

        #처리시간 체크
        time_check = time.time() - start

        doc = {
                "url" : url,
                "words" : words,
                "count" : count,
                "count2" : count2,
                "time" : time_check,
        }

        global id_count
        id_count += 1

        es.index(index="ll", doc_type="ex", id=id_count, body=doc)

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

                cnt = id_count #현재 출력된 문서의 개수

                web_crawling(url)

                for i in range(cnt+1, id_count+1, 1):
                        res = es.get(index="ll", doc_type="ex", id=i)

                        d = {}
                        d['url'] = res['_source']['url']
                        d['words'] = res['_source']['words']
                        d['count'] = res['_source']['count']
                        d['count2'] = res['_source']['count2']
                        d['time'] = res['_source']['time']

                        craw_list.append(d)

                #새롭게 구하기 위해서
                del vector_list[:]
                #id_count가 1일때는 안해야함?
                for i in range(1, id_count+1, 1):
                        res = es.get(index="ll", doc_type="ex", id=i)
                        url = res['_source']['url']
                        words = res['_source']['words']
                        vector_list.append(make_vector(url, words))

                cosine()

                ######

                idf_dic = idf()

                tfidf_list = []
                tfidf_list = tfidf(idf_dic)

                vector_dic = make_vector()
                cosine(vector_dic)

                #crawl 결과를 output.html로 리턴
                return render_template('txtout2.html', craw_list = craw_list, cosine_s = cosine_s, tfidf_list= tfidf_list)

@app.route('/txt_url',methods = ['POST','GET'])
def txt_url():
        if request.method == 'POST':
                #text file이름을 받아옴
                txt=request.form['textname']

                #test_txt폴더에 있는 txt파일들중 이름이 같은 파일을 찾아서 파일을 연다
                f = open("./test_txt/"+txt+".txt",'r')
                #거기에 있는 URL을 list로 받음
                cnt = id_count
                while True:
                        line = f.readline()
                        if not line: break

                        url_list.append(line)
                        web_crawling(line)

                for i in range(cnt+1, id_count+1, 1):
                        res = es.get(index="ll", doc_type="ex", id=i)

                        d = {}

                        d['url'] = res['_source']['url']
                        d['words'] = res['_source']['words']
                        d['count'] = res['_source']['count']
                        d['count2'] = res['_source']['count2']
                        d['time'] = res['_source']['time']

                        craw_list.append(d)


                f.close()

                #새롭게 구하기 위해서
                del vector_list[:]
                for i in range(1, id_count+1, 1):
                        res = es.get(index="ll", doc_type="ex", id=i)
                        url = res['_source']['url']
                        words = res['_source']['words']
                        vector_list.append(make_vector(url, words))

                cosine()
                print cosine_s

                #############

                for i in range(1, id_count+1, 1):
                        res = es.get(index="ll", doc_type="ex", id=i)

                        words = res['_source']['words']
                        count = res['_source']['count']
                        tf_list.append(tF(words, count))


                idf_dic = idf()

                tfidf_list = []

                tfidf_list = tfidf(idf_dic)
                print len(tfidf_list)

                #vector_dic = make_vector()
                #cosine(vector_dic)

                #url리스트들을 txtout.html로 넘김
                return render_template('txtout2.html', craw_list = craw_list , tfidf_list=tfidf_list)

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



        
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     1,1           Top
