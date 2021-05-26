import requests

#for verdict
dirw = "C:\\Users\\ryanp\\Desktop\\amir_half.mp4"
url_vid = "http://127.0.0.1:5000/dfapi"
files = {'video' : open(dirw,'rb')}
#response = requests.post(url,files=files)

#for data
url_data = 'http://127.0.0.1:5000/dfapi/data'

response_d = requests.request(url=url_data)


print(response.text)
