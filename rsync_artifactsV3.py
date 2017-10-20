import requests
import bs4

source_repo = "http://35.197.136.44:8081/artifactory/PrasanthKatta"
destination_repo = "http://35.197.136.44:8081/artifactory/Maven_Project_1"
source_auth = ('test', 'test123')
destination_auth = ('test', 'test123')

source_actually_data = []
destination_actually_date = []


def give_me_bs4_soup(url=None, authentication=None):
    if url and authentication:
        res = requests.get(url, auth=authentication)
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        root_data = soup.find_all('a', href=True)
        return root_data
    else:
        print 'get_raw_data_from_url Function takes 2 arguments\n\'' \
              'url= from which url you need\n\'' \
              'authentication= credentials of the url to access'


def get_raw_html_data_for_url(url=None, authentication=None):
    if url and authentication:
        root_level_data = give_me_bs4_soup(url, authentication=authentication)
        dirs_data = []
        file_data = []
        for each_data in root_level_data:
            if each_data.text.endswith('/'):
                dirs_data.append(url + '/' + each_data.text)
            else:
                file_data.append(url + '/' + each_data.text)
        while True:
            if dirs_data:
                print "running max depth"
            else:
                break
    else:
        print 'get_raw_data_from_url Function takes 2 arguments\n\'' \
              'url= from which url you need\n\'' \
              'authentication= credentials of the url to access'


print get_raw_html_data_for_url(url=source_repo, authentication=source_auth)