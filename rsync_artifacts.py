from artifactory import ArtifactoryPath

source_repo = "http://31.18.25.20:8081/artifactory/PrasanthKatta"
destination_repo = "http://35.17.25.22:8081/artifactory/Maven_Project_1"
source_auth = ('a', 'b')
destination_auth = ('a', 'b')

connect_source = ArtifactoryPath(source_repo,
                                 auth=source_auth)

connect_destination = ArtifactoryPath(destination_repo,
                                      auth=destination_auth)
print "From Source"
for p in connect_source:
    print p
print "From Destination"
for dp in connect_destination:
    print dp
