#!/usr/bin/env python
"""
Documentation :
This scritp was will perform Rsync between 2
JFrog artifactories
1. this script will first compare the both artifacts
2. second take artifacts which are not present on destination
and copy them to destination
3. third it will also check for deleted files on source and will
delete the same files from destination as well
Author: Prasanth Katta
Date: 9 Oct 2017
Version: 1.0
Team: DevOps (CTCO-FGLS)
"""
from artifactory import ArtifactoryPath, walk
from re import compile
from os import path, makedirs, chdir, unlink, stat, listdir
from datetime import datetime
from time import time
from shutil import rmtree
from logging import info, error, warn, basicConfig, debug

TEMP_PATH_ = 'C:\Users\Prasanth_Katta\Downloads'
source_artifacts_url = 'http://35.197.136.44:8081/artifactory/Maven_Project_3'
destination_artifacts_url = 'http://35.197.136.44:8081/artifactory/Maven_Project_1'
source_artifacts_credentials = ('test', 'test123')
destination_artifacts_credentials = ('test', 'test123')
TEMP_PATH_DATE = 'TEMP_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
TEMP_Path = path.abspath(path.join(TEMP_PATH_, TEMP_PATH_DATE))
LOGS_PATH = path.abspath(path.join(TEMP_Path, 'logs'))
if not path.exists(path.abspath(LOGS_PATH)):
    print "Creating Logs Dirs"
    try:
        makedirs(path.abspath(LOGS_PATH))
    except Exception as e:
        print '[ERROR]: Unable to Create Logs Dir'
        print '[ERROR INFO]: %s' % e

try:
    source_connect = ArtifactoryPath(source_artifacts_url,
                                     auth=source_artifacts_credentials)
except Exception as e:
    print '[ERROR]: Unable to connect to Source: %s' % source_artifacts_url
    print '[ERROR INFO]: %s' % e

try:
    destination_connect = ArtifactoryPath(destination_artifacts_url,
                                          auth=destination_artifacts_credentials)
except Exception as e:
    print '[ERROR]: Unable to connect to destination: %s' % destination_artifacts_url
    print '[ERROR INFO]: %s' % e

# Trying to get the max depth path and artifacts
source_max_depth_Regex = compile(r'%s(.*)' % source_artifacts_url)
destination_max_depth_Regex = compile(r'%s(.*)' % destination_artifacts_url)


def check_permissions_to_access_artifacts(uri_for_permissions=None, u_name=None):
    if uri_for_permissions and u_name:
        print '[INFO] : Checking for User Permissions for the artifact'
        print '[INFO] : %s' % uri_for_permissions
        print uri_for_permissions.properties


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
print list(source_info)
source_extended_info = get_required_extended_links_only(artifact_full_link_data=source_info,
                                                        regex_connect=source_max_depth_Regex)
print list(source_extended_info)
destination_info = get_artifacts_full_data(uri=destination_connect)
print list(destination_info)
destination_extended_info = get_required_extended_links_only(artifact_full_link_data=destination_info,
                                                             regex_connect=destination_max_depth_Regex)
print list(destination_extended_info)


def _synchronization_from_scr_to_destination():
    print 'synchronization from source: %s' \
          'to destination: %s in progress' \
                  % (source_artifacts_url, destination_artifacts_url)
    print '[INFO] : artifacts present in source and not in destination'
    source_but_not_destination = source_extended_info - destination_extended_info
    if source_but_not_destination:
        print list(source_but_not_destination)
    else:
        print "[INFO] : Both Source and Destination are already in sync. No action required."
    for artifacts_not_in_destination in source_but_not_destination:
        main_source = source_artifacts_url + artifacts_not_in_destination
        _path = ArtifactoryPath(main_source, auth=source_artifacts_credentials)
        f_name = str(_path).split('/')[-1]
        f_full_path = [p for p in str(artifacts_not_in_destination).split('/')[:-1] if p]
        if f_full_path:
            print '/'.join(f_full_path)
        if not path.exists(path.abspath(TEMP_Path)):
            try:
                makedirs(path.abspath(TEMP_Path))
            except Exception as dirs_errors:
                print '[ERROR]: Unable to Create dirs'
                print '[ERROR INFO]: %s' % dirs_errors
        if f_full_path:
            download_path = path.abspath(path.join(TEMP_Path, '/'.join(f_full_path)))
        else:
            download_path = path.abspath(path.join(TEMP_Path))
        if not path.exists(path.abspath(download_path)):
            try:
                makedirs(path.abspath(download_path))
            except Exception as dirs_errors:
                print '[ERROR]: Unable to create dirs'
                print '[ERROR INFO]: %s' % dirs_errors
        print download_path
        print "Please wait. Downloading the artifacts: %s" % _path
        with _path.open() as fd:
            with open(path.abspath(path.join(download_path, f_name)), "wb") as out:
                out.write(fd.read())
        if f_full_path:
            change_new_path = destination_artifacts_url + '/' + '/'.join(f_full_path)
            print "Creating new path on destination Side: %s" % change_new_path
            d_path = ArtifactoryPath(change_new_path, auth=destination_artifacts_credentials)
            if not d_path.exists():
                d_path.mkdir()
        else:
            d_path = ArtifactoryPath(destination_artifacts_url, auth=destination_artifacts_credentials)
        print "deploying the artifact to destination: %s" % d_path
        d_path.deploy_file(path.abspath(path.join(download_path, f_name)))


def _synchronization_for_deleted_items():
    print 'artifacts present in destination: %s' \
          'and not in source: %s' % (source_artifacts_url,
                                     destination_artifacts_url)
    destination_but_not_source = destination_extended_info - source_extended_info
    if destination_but_not_source:
        print list(destination_but_not_source)
    else:
        print "[INFO]: Both Source and destination are in sync. No deleting/removal required"
    if destination_but_not_source:
        for each_destination_deleted_artifact in destination_but_not_source:
            print "[INFO]: We have below artifact deleted from source."
            print "[INFO] : Deleting following artifact from destination " \
                  "as its removed from source " \
                  "artifacts : %s" % each_destination_deleted_artifact
            destination_removal_url = destination_artifacts_url + each_destination_deleted_artifact
            print destination_removal_url
            destination_removal_uri = ArtifactoryPath(destination_removal_url,
                                                      auth=destination_artifacts_credentials)
            if destination_removal_uri.is_dir():
                print "[INFO] : Removing destination dir tree"
                print '[INFO] : %s' % destination_removal_uri
                destination_removal_uri.rmdir()
            elif destination_removal_uri.is_file():
                print "[INFO] : Removing destination artifact files"
                print '[INFO] : %s' % destination_removal_uri
                destination_removal_uri.unlink()
            else:
                print '[IMP INFO] : Some New type of file please add this'
                print '[IMP INFO] : %s' % destination_removal_uri


def trash_old_files_folders(path_=None, number_of_days=None):
    time_in_sec = time.time() - (number_of_days * 24 * 60 * 60)
    file_count = 0
    dir_count = 0
    total = 0
    c = 1
    if path.exists(path):
        logging.info('checking path exist or not -> %s', path)
        for content in listdir(path):
            file_m_time = stat(path.join(path, content))
            logging.info('Getting file modified time -> %s', file_m_time)
            if file_m_time.st_mtime <= time_in_sec:
                if path.isdir(path.join(path, content)):
                    chdir(path)
                    c += 1
                    try:
                        rmtree(content)
                        logging.info('Removing Dir -> %s', content)
                    except Exception as e:
                        print 'Error: unable to remove dir -> %s' % e
                        logging.error('unable to remove dir -> %s', e)
                    else:
                        dir_count += 1
                        print 'Cleaning From System -> %s' % content
                        logging.debug('Cleaning From System -> %s', content)
                else:
                    chdir(path)
                    c += 1
                    try:
                        unlink(content)
                        logging.info('Removing File-> %s', content)
                    except Exception as e:
                        print 'Error: unable to remove file -> %s' % e
                        logging.error('unable to remove file -> %s', e)
                    else:
                        file_count += 1
                        print 'Cleaning From System -> %s' % content
                        logging.debug('Cleaning From System -> %s', content)
                total += 1
        print 'Summery'.center(40, '*')
        print 'Total files removed -> %s' % file_count
        logging.debug('Total files removed -> %s', file_count)
        print 'Total dirs removed -> %s' % dir_count
        logging.debug('Total dirs removed -> %s', dir_count)
        print 'Total removed -> %s' % total
        logging.debug('Total removed -> %s', total)
        return file_count, dir_count, total


if __name__ == '__main__':
    _synchronization_from_scr_to_destination()
    _synchronization_for_deleted_items()
