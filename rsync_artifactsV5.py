from artifactory import ArtifactoryPath, walk
import re
import os
import sys

TEMP_Path = os.path.abspath(os.path.join('C:\Users\Prasanth_Katta\Downloads', 'TEMP'))
print TEMP_Path
source_artifacts_url = 'http://35.198.202.31:8081/artifactory/Maven_Project_1'
destination_artifacts_url = 'http://35.198.202.31:8081/artifactory/Maven_Project_2'
source_artifacts_credentials = ('test', 'test123')
destination_artifacts_credentials = ('test', 'test123')

source_connect = ArtifactoryPath(source_artifacts_url,
                                 auth=source_artifacts_credentials)

destination_connect = ArtifactoryPath(destination_artifacts_url,
                                      auth=destination_artifacts_credentials)

source_max_depth_Regex = re.compile(r'%s(.*)' % source_artifacts_url)

destination_max_depth_Regex = re.compile(r'%s(.*)' % destination_artifacts_url)


def get_artifacts_full_data(uri=None):
    artifacts_data = []
    if uri:
        for link in walk(uri, topdown=True):
            if link[2]:
                for extended_links in link[2]:
                    if str(link[0]).endswith('/'):
                        artifacts_data.append(str(link[0]) + extended_links)
                    else:
                        artifacts_data.append(str(link[0]) + '/' + extended_links)
    return artifacts_data


def get_required_extended_links_only(artifact_full_link_data=None, regex_connect=None):
    filter_artifacts_data = set()
    if artifact_full_link_data and regex_connect:
        for each_link in artifact_full_link_data:
            filter_artifacts_data.add(regex_connect.search(each_link).groups()[0])
    return filter_artifacts_data


source_info = get_artifacts_full_data(uri=source_connect)
print source_info
source_extended_info = get_required_extended_links_only(artifact_full_link_data=source_info,
                                                        regex_connect=source_max_depth_Regex)
print source_extended_info
destination_info = get_artifacts_full_data(uri=destination_connect)
print destination_info
destination_extended_info = get_required_extended_links_only(artifact_full_link_data=destination_info,
                                                             regex_connect=destination_max_depth_Regex)
print destination_extended_info

print 'rsync between artifacts inprogress..'
print 'artifacts present in source and not in destination'
source_but_not_destination = source_extended_info - destination_extended_info
print source_but_not_destination
for sbnd in source_but_not_destination:
    main_source = source_artifacts_url + sbnd
    path = ArtifactoryPath(main_source, auth=source_artifacts_credentials)
    f_name = str(path).split('/')[-1]
    print f_name
    f_full_path = [p for p in str(sbnd).split('/')[:-1] if p]
    print '/'.join(f_full_path)
    if not os.path.exists(os.path.abspath(TEMP_Path)):
        os.makedirs(os.path.abspath(TEMP_Path))
    if f_full_path:
        download_path = os.path.abspath(os.path.join(TEMP_Path, '/'.join(f_full_path)))
    else:
        download_path = os.path.abspath(os.path.join(TEMP_Path))
    if not os.path.exists(os.path.abspath(download_path)):
        os.makedirs(os.path.abspath(download_path))
    print download_path
    print "downloading the artifacts.. Please wait"
    with path.open() as fd:
        with open(os.path.abspath(os.path.join(download_path, f_name)), "wb") as out:
            out.write(fd.read())
    d_full_path = destination_artifacts_url + sbnd
    if f_full_path:
        print "Creating new path on destination Side"
        change_new_path = destination_artifacts_url + '/' + '/'.join(f_full_path)
        d_path = ArtifactoryPath(change_new_path, auth=destination_artifacts_credentials)
        d_path.mkdir()
    else:
        d_path = ArtifactoryPath(destination_artifacts_url, auth=destination_artifacts_credentials)
    print "deploying the artifact to destination"
    d_path.deploy_file(os.path.abspath(os.path.join(download_path, f_name)))
print 'artifacts presnet in destination and not in source'
print destination_extended_info - source_extended_info