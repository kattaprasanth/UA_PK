from artifactory import ArtifactoryPath
import requests
import bs4

source_repo = "http://35.197.136.44:8081/artifactory/PrasanthKatta"
destination_repo = "http://35.197.136.44:8081/artifactory/Maven_Project_1"
source_auth = ('test', 'test123')
destination_auth = ('test', 'test123')
content_types = ['text/html']

connect_source = ArtifactoryPath(source_repo,
                                 auth=source_auth)

print connect_source.iterdir()
for d in connect_source.iterdir():
    print d