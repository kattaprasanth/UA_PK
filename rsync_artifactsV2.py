import requests
import bs4

source_repo = "http://35.187.251.202:8081/artifactory/PrasanthKatta"
destination_repo = "http://35.187.251.202:8081/artifactory/Maven_Project_1"
source_auth = ('test', 'test123')
destination_auth = ('test', 'test123')
content_types = ['text/html']

res = requests.get(source_repo, auth=source_auth)
print res.status_code
soup = bs4.BeautifulSoup(res.text, "html.parser")
data = soup.findAll("a")
for d in data[1:]:
    if d.text.endswith('/'):
        print 'Dirs here'
        print d.attrs['href']
    else:
        print 'Only Files'
        print d.text