import os
import sys
import urllib
import json
import tweepy
from flask import Flask, jsonify
from tweepy.parsers import JSONParser
from multiprocessing import Process, Queue

app = Flask(__name__)

TWITTER_API_KEY = "Replace this string with your twitter api key"
TWITTER_API_SECRET = "Replace this string with your twitter api secret key"
GOOGLE_API_KEY = "Replace this string with your google api key"
GOOGLE_API_CX = "Replace this string with your google api cx"


auth = tweepy.AppAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
api = tweepy.API(auth,
			   wait_on_rate_limit=True,
			   wait_on_rate_limit_notify=True,
			   parser=tweepy.parsers.JSONParser()
			   )
if (not api):
	print ("Can't Authenticate Twitter")
	sys.exit (-1)


#For storing the results of the three following parallel functions
result_queue = Queue()		


#DuckDuckGo instant API
def ddg(query):
	ddg_result = {
		"duckduckgo": {
			"url": "", 
			"text": ""
		 }
	}
	ddg_url = "https://api.duckduckgo.com/?q=%s&format=json&pretty=1" % query 
	ddg_response = urllib.urlopen(ddg_url)
	temp1 = json.loads(ddg_response.read())
	try:
		ddg_result = {
			"duckduckgo": {
				"url": ddg_url,
				"text": temp1["AbstractText"]
			 }
		}
	except Exception:
		pass
	result_queue.put(ddg_result)


#Google Search API
def google(query):
	google_result = {
		"google": {
			"url": "", 
			"text": ""
		}
	}
	google_url = "https://www.googleapis.com/customsearch/v1?key=%s&cx=%s&q=%s&fields=items/pagemap/website/description" % (GOOGLE_API_KEY,GOOGLE_API_CX,query)
	google_response = urllib.urlopen(google_url)
	temp2 = json.loads(google_response.read())
	try:
		google_result = {
			"google": {
				"url": google_url,
				"text": temp2["items"][0]["pagemap"]["website"][0]["description"]
			}
		}
	except Exception:
		pass
	result_queue.put(google_result)


#Twitter API
def twitter(query):
	twitter_text=""
	twitter_result = {
		"twitter": {
			"url": "",
			"text": ""
		}
	}
	twitter_response = api.search(q=query, count=1)
	try:
		twitter_text = twitter_response["statuses"][0]["text"]
	except Exception:
		pass
	result_queue.put(
		{
			"twitter": {
				"url": "", 
				"text": twitter_text
			}
		}	
	)


@app.route("/")
def index():
	return """
			<html>
			<body style='font-family="Helvetica, sans-serif"'>
			<h1>Quick Search</h1>
			<h4>Multiple Resource Search REST API using Python</h4> <br>
			<h3>About</h3>
			<p>This API searches for a query on Google, Twitter and DuckDuckGo in parallel 
			using multiprocessing module of python and gives a combined result quickly which
			contains the description from these three engines in JSON format.
			</p>
			<br>
			<h3>Usage</h3>
			To use it Please follow the following syntax : <br>
			<p>curl https://quick-search.herokuapp.com//THE_QUERY_TO_BE_SEARCHED<p>
			<br>
			<h3><a href="https://github.com/prince-chauhan/Quick-Search">Link to its code on Github</a></h3>
			<br>
			<br>
				<footer class="footer">
				<br>
					Contact : <br>
					Name : Prince Chauhan<br>
					Email : princechauhan800@gmail.com<br>
					<div class="w3l-social">
						<p>Connect to me on  
							<a href="https://in.linkedin.com/in/princechauhan1" target="_blank"><i class="fa fa-linkedin fa-lg"> Linkedin</i></a>
						</p>
					</div>

				</footer>
			</body>
			</html>
			"""			

@app.route("/<query>")
def main(query):
	p1 = Process(target=ddg, args=(query,))
	p1.start()
	p2 = Process(target=google, args=(query,))
	p2.start()
	p3 = Process(target=twitter, args=(query,))
	p3.start()
	
	p1.join()
	p2.join()
	p3.join()

	result = {"query": query,
			"results": [
				result_queue.get(),
				result_queue.get(),
				result_queue.get()
			]
		}

	return jsonify(result)


if __name__ == "__main__":
	app.run(debug=True)
