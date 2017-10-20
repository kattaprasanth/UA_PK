from requests import get
from json import loads
from artifactory import ArtifactoryPath
import  datetime
#uri = get('http://35.197.136.44:8081/artifactory/ui/artifactpermissions?repoKey=PrasanthKattaKumar',
#          auth=('test', 'test123'))

#print uri.status_code

#print loads(uri.text)['userEffectivePermissions'][0]['permission']

con = ArtifactoryPath('http://35.198.202.31:8081/artifactory/Maven_Project_3/org.zip',
                      auth=('test', 'test123'))

my_date = '2017-11-12'
second_date = '2017-10-13'


a = set(['a', 'p', 'k', 'h'])
b = set(['p', 'e', 'f', 'h'])


#print con.stat()[1]
#print str(con.stat()[1]).split()[0]
#print str(con.stat()[1]).split()[1].split('+')[0]

if second_date >= my_date:
    print 'got greater date for second'


def get_artifacts_modified_date_and_time(uri=None, credentials=None):
    if uri and credentials:
        e_link = ArtifactoryPath(uri, auth=credentials)
        artifact_modified_date = str(e_link.stat()[1]).split()[0]
        # print artifact_modified_date
        artifact_modified_time = str(e_link.stat()[1]).split()[1].split('+')[0]
        # print artifact_modified_time
        if artifact_modified_date and artifact_modified_time:
            return artifact_modified_date, artifact_modified_time
        else:
            return exit(1)


test = ['/org.zip', '/spring/spring/1.0/spring-1.0.jar']

for e in test:
    print len(e.split('/'))


ul = 'http://35.197.136.44:8081/artifactory/Maven_Project_7/com/pk'
print ul
import re
r = re.compile(r'(.*)artifactory/(.*)')
rp = str(r.search(ul).groups()[1]).split('/')[0]
print rp