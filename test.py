from artifactory import ArtifactoryPath, walk
import re

s = re.compile(r'http://35.198.202.31:8081/artifactory/PrasanthKatta(.*)')

con = ArtifactoryPath('http://35.198.202.31:8081/artifactory/PrasanthKatta',
                      auth=('test', 'test123'))

data = []

for link in walk(con, topdown=True):
    if link[2]:
        for ee in link[2]:
            if str(link[0]).endswith('/'):
                data.append(str(link[0]) + ee)
            else:
                data.append(str(link[0]) + '/' + ee)

filter_source = []

for each_link in data:
    filter_source.append(s.search(each_link).groups()[0])

print filter_source