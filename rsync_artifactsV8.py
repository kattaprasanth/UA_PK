#!/usr/bin/env python

"""
Documentation :
This script was will perform Rsync between 2
JFrog artifactory
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
from os import path, makedirs, chdir, unlink, stat, listdir, chdir
from datetime import datetime
from time import time
from shutil import rmtree
from logging import info, error, warn, basicConfig, debug, DEBUG
from requests import get
from json import loads
from sys import exit

TEMP_PATH_ = 'C:\Users\Prasanth_Katta\Downloads\TEMP'
source_artifacts_url = 'http://35.198.202.31:8081/artifactory/Maven_Project_3'
destination_artifacts_url = 'http://35.198.202.31:8081/artifactory/Maven_Project_2'
source_artifacts_credentials = ('test', 'test123')
destination_artifacts_credentials = ('test', 'test123')
TEMP_PATH_DATE = 'TEMP_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
TEMP_Path = path.abspath(path.join(TEMP_PATH_, TEMP_PATH_DATE))
LOGS_PATH = path.abspath(path.join(TEMP_Path, 'logs'))
LOGS_PATH_FILE = path.abspath(
    path.join(LOGS_PATH, '%s'
              % (datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.log')))
if not path.exists(path.abspath(LOGS_PATH)):
    print "Creating Logs Dirs"
    try:
        makedirs(path.abspath(LOGS_PATH))
    except Exception as e:
        print '[ERROR]: Unable to Create Logs Dir'
        print '[ERROR INFO]: %s' % e

if not path.exists(path.abspath(LOGS_PATH_FILE)):
    open(path.abspath(LOGS_PATH_FILE), 'w').close()
basicConfig(format=('%(asctime)s - %(levelname)s - %(message)s'),
            datefmt='%m/%d/%Y %I:%M:%S %p',
            filename='%s' % LOGS_PATH_FILE,
            level=DEBUG)

try:
    source_connect = ArtifactoryPath(source_artifacts_url,
                                     auth=source_artifacts_credentials)
except Exception as e:
    print '[ERROR]: Unable to connect to Source: %s' % source_artifacts_url
    print '[ERROR INFO]: %s' % e
    error('Unable to connect to Source: %s' % source_artifacts_url)
    error(e)

try:
    destination_connect = ArtifactoryPath(destination_artifacts_url,
                                          auth=destination_artifacts_credentials)
except Exception as e:
    print '[ERROR]: Unable to connect to destination: %s' % destination_artifacts_url
    print '[ERROR INFO]: %s' % e
    error('Unable to connect to destination: %s' % destination_artifacts_url)
    error(e)

# Trying to get the max depth path and artifacts
source_max_depth_Regex = compile(r'%s(.*)' % source_artifacts_url)
destination_max_depth_Regex = compile(r'%s(.*)' % destination_artifacts_url)


def check_permissions_to_access_destination_artifacts(uri_for_permissions=None):
    if uri_for_permissions:
        print '[INFO] : Checking for User Permissions for the artifact'
        print '[INFO] : %s' % uri_for_permissions
        info('Checking for User Permissions for the artifact')
        info(uri_for_permissions)
        repo = str(uri_for_permissions).split('/')[-1:][0]
        repo_uri = compile(r'(.*)artifactory')
        if repo_uri.search(uri_for_permissions).group():
            print 'check Repository permissions on destination side'
            info('check Repository permissions on destination side')
            _uri_for_permission = repo_uri.search(uri_for_permissions).group() + \
                '/ui/artifactpermissions?repoKey=' + repo
            debug(_uri_for_permission)
            res = get(_uri_for_permission, auth=destination_artifacts_credentials)
            if res.status_code == 200:
                print 'Successfully connect to destination to check permissions'
                info('Successfully connect to destination to check permissions')
                permission_data = loads(res.text)['userEffectivePermissions'][0]['permission']
                debug(permission_data)
                if permission_data['read'] and permission_data['deploy']:
                    print 'User Have Read and Deploy permissions'
                    debug('User Have Read and Deploy permissions')
                else:
                    print 'User Do not have permissions'
                    error('User Do not have permissions')
                    exit(1)
                if permission_data['delete']:
                    print 'User Also has Delete Permissions to read and deploy'
                    debug('User Also has Delete Permissions to read and deploy')
                else:
                    print 'User do not have permissions to delete'
                    error('User do not have permissions to delete')
                    exit(1)


def get_artifacts_full_data(uri=None):
    artifacts_data = []
    if uri:
        for link in walk(uri, topdown=True):
            debug('Walking the max depth artifacts paths')
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
debug(list(source_extended_info))
destination_info = get_artifacts_full_data(uri=destination_connect)
print list(destination_info)
destination_extended_info = get_required_extended_links_only(artifact_full_link_data=destination_info,
                                                             regex_connect=destination_max_depth_Regex)
debug(list(destination_extended_info))


def _synchronization_of_same_file_to_latest_one():
    same_artifacts_on_both = source_extended_info.intersection(destination_extended_info)
    if same_artifacts_on_both:
        print '[INFO] : we have artifacts present on source and destination'
        info('we have artifacts present on source and destination')
        print '[INFO] : checking they last modified time to sync again'
        info('checking last modified time to sync with destination')
        print list(same_artifacts_on_both)
        for each_modified_artifacts in same_artifacts_on_both:
            modified_source_artifact_uri = source_artifacts_url + each_modified_artifacts
            print modified_source_artifact_uri
            modified_source_artifacts = ArtifactoryPath(modified_source_artifact_uri, auth=source_artifacts_credentials)
            destination_artifact_date_older_then_source = False
            destination_artifact_time_older_then_source = False
            if modified_source_artifacts.stat()[1]:
                print 'collecting modified details of the source artifact'
                modified_source_artifact_date = str(modified_source_artifacts.stat()[1]).split()[0]
                modified_source_artifact_time = str(modified_source_artifacts.stat()[1]).split('+')[0]
                if modified_source_artifact_date and modified_source_artifact_time:
                    print 'we got both modified data and time of source artifact'
                    print modified_source_artifact_date
                    print modified_source_artifact_time
                else:
                    print "[ERROR]: Unable to get source artifact data and time."
                    error("[ERROR]: Unable to get source artifact data and time.")
            else:
                print "[ERROR]: Unable to get source artifact data and time."
                error("[ERROR]: Unable to get source artifact data and time.")
            modified_destination_artifact_uri = destination_artifacts_url + each_modified_artifacts
            modified_destination_artifacts = ArtifactoryPath(modified_destination_artifact_uri,
                                                             auth=destination_artifacts_credentials)
            if modified_destination_artifacts.stat()[1]:
                print 'Collecting modified details from the destination artifact'
                modified_destination_artifact_date = str(modified_destination_artifacts.stat()[0]).split()[0]
                modified_destination_artifact_time = str(modified_destination_artifacts.stat()[0]).split('+')[0]
                if modified_source_artifact_date and modified_destination_artifact_time:
                    print 'we got both date and time from destination artifact'
                    print modified_destination_artifact_date
                    print modified_destination_artifact_time
            else:
                print '[ERROR]: Unable to get source artifact data and time.'
                error('[ERROR]: Unable to get source artifact data and time.')
            if modified_destination_artifact_date >= modified_source_artifact_date:
                print 'we see destination artifacts Date is up to date. no SYNC needed'
            else:
                destination_artifact_date_older_then_source = True
            if modified_destination_artifact_time >= modified_source_artifact_time:
                print 'we see destination artifacts Time is up to date. no SYNC needed'
            else:
                destination_artifact_time_older_then_source = True
            if destination_artifact_date_older_then_source and destination_artifact_time_older_then_source:
                print '[HIGH IMP] : updating destination artifacts to latest'
                print 'Destination artifacts are getting updates to latest as source'
                print modified_destination_artifact_uri
                print 'Downloading source artifact to disk to update on destination destination'
                modified_download_path = path.abspath(path.join(TEMP_Path, 'modified_artifacts'))
                if not path.exists(path.abspath(modified_download_path)):
                    makedirs(modified_download_path)
                artifact_name = str(each_modified_artifacts).split('/')[-1]
                modified_artifact_download_path = [p for p in str(each_modified_artifacts).split('/')[:-1] if p]
                if modified_artifact_download_path:
                    print '/'.join(modified_artifact_download_path)
                    m_path = '/'.join(modified_artifact_download_path)
                    if not path.exists(path.abspath(path.join(modified_download_path, m_path))):
                        print 'created required path on disk'
                        makedirs(path.abspath(path.join(modified_download_path, m_path)))
                        download_path_ = path.abspath(path.join(modified_download_path, m_path))
                else:
                    download_path_ = path.abspath(modified_download_path)
                with modified_source_artifacts.open() as fb:
                    with open(path.join(download_path_, artifact_name), 'wb') as out:
                        out.write(fb.read())
                print 'Uploading latest artifact to destination'
                if modified_artifact_download_path:
                    print 'uploading artifacts to: %s' % '/'.join(modified_artifact_download_path)
                    modified_upload_uri = modified_destination_artifact_uri + '/'.join(modified_artifact_download_path)
                else:
                    modified_upload_uri = modified_destination_artifact_uri
                print 'upload uri : %s' % modified_upload_uri
                _upload_destination_uri = ArtifactoryPath(modified_upload_uri, auth=destination_artifacts_credentials)
                chdir(path.abspath(download_path_))
                _upload_destination_uri.deploy_file(artifact_name)


def _synchronization_from_scr_to_destination():
    print 'synchronization from source: %s ' \
          'to destination: %s in progress ' \
                  % (source_artifacts_url, destination_artifacts_url)
    print '[INFO] : artifacts present in source and not in destination'
    info('artifacts present in source and not in destination')
    source_but_not_destination = source_extended_info - destination_extended_info
    if source_but_not_destination:
        print list(source_but_not_destination)
    else:
        print "[INFO] : Both Source and Destination are already in sync. No action required."
        info("Both Source and Destination are already in sync. No action required.")
    for artifacts_not_in_destination in source_but_not_destination:
        main_source = source_artifacts_url + artifacts_not_in_destination
        _path = ArtifactoryPath(main_source, auth=source_artifacts_credentials)
        f_name = str(_path).split('/')[-1]
        info(f_name)
        f_full_path = [p for p in str(artifacts_not_in_destination).split('/')[:-1] if p]
        if f_full_path:
            print '/'.join(f_full_path)
        if not path.exists(path.abspath(TEMP_Path)):
            try:
                makedirs(path.abspath(TEMP_Path))
            except Exception as dirs_errors:
                print '[ERROR]: Unable to Create dirs'
                print '[ERROR INFO]: %s' % dirs_errors
                error('Unable to Create dirs')
                error(dirs_errors)
        if f_full_path:
            download_path = path.abspath(path.join(TEMP_Path, '/'.join(f_full_path)))
            debug(download_path)
        else:
            download_path = path.abspath(path.join(TEMP_Path))
            debug(download_path)
        if not path.exists(path.abspath(download_path)):
            try:
                makedirs(path.abspath(download_path))
            except Exception as dirs_errors:
                print '[ERROR]: Unable to create dirs'
                print '[ERROR INFO]: %s' % dirs_errors
                error('Unable to create dirs')
                error(dirs_errors)
        print download_path
        print "Please wait. Downloading the artifacts: %s" % _path
        debug("Please wait. Downloading the artifacts: %s" % _path)
        with _path.open() as fd:
            with open(path.abspath(path.join(download_path, f_name)), "wb") as out:
                out.write(fd.read())
        if f_full_path:
            change_new_path = destination_artifacts_url + '/' + '/'.join(f_full_path)
            print "Creating new path on destination Side: %s" % change_new_path
            debug("Creating new path on destination Side: %s" % change_new_path)
            d_path = ArtifactoryPath(change_new_path, auth=destination_artifacts_credentials)
            if not d_path.exists():
                d_path.mkdir()
        else:
            d_path = ArtifactoryPath(destination_artifacts_url, auth=destination_artifacts_credentials)
        print "deploying the artifact to destination: %s" % d_path
        debug("deploying the artifact to destination: %s" % d_path)
        d_path.deploy_file(path.abspath(path.join(download_path, f_name)))


def _synchronization_for_deleted_items():
    print 'artifacts present in destination: %s ' \
          'and not in source: %s' % (source_artifacts_url,
                                     destination_artifacts_url)
    destination_but_not_source = destination_extended_info - source_extended_info
    if destination_but_not_source:
        print list(destination_but_not_source)
        debug(list(destination_but_not_source))
    else:
        print "[INFO]: Both Source and destination are in sync. No deleting/removal required"
        info('Both Source and destination are in sync. No deleting/removal required')
    if destination_but_not_source:
        for each_destination_deleted_artifact in destination_but_not_source:
            print "[INFO]: We have below artifact deleted from source."
            print "[INFO] : Deleting following artifact from destination " \
                  "as its removed from source " \
                  "artifacts : %s" % each_destination_deleted_artifact
            debug('Deleting following artifact from destination')
            debug("artifacts : %s" % each_destination_deleted_artifact)
            destination_removal_url = destination_artifacts_url + each_destination_deleted_artifact
            print destination_removal_url
            destination_removal_uri = ArtifactoryPath(destination_removal_url,
                                                      auth=destination_artifacts_credentials)
            if destination_removal_uri.is_dir():
                print "[INFO] : Removing destination dir tree"
                debug('Removing destination dir tree')
                print '[INFO] : %s' % destination_removal_uri
                debug('%s' % destination_removal_uri)
                destination_removal_uri.rmdir()
            elif destination_removal_uri.is_file():
                print "[INFO] : Removing destination artifact files"
                debug("Removing destination artifact files")
                print '[INFO] : %s' % destination_removal_uri
                debug('%s' % destination_removal_uri)
                destination_removal_uri.unlink()
            else:
                print '[IMP INFO] : Some New type of file please add this'
                warn('[IMP INFO] : Some New type of file please add this')
                print '[IMP INFO] : %s' % destination_removal_uri
                warn('[IMP INFO] : %s' % destination_removal_uri)


def trash_old_files_folders(path_=None, number_of_days=None):
    time_in_sec = time() - (number_of_days * 24 * 60 * 60)
    file_count = 0
    dir_count = 0
    total = 0
    c = 1
    if path.exists(path_):
        info('checking path exist or not -> %s', path_)
        for content in listdir(path_):
            file_m_time = stat(path.join(path_, content))
            info('Getting file modified time -> %s', file_m_time)
            if file_m_time.st_mtime <= time_in_sec:
                if path.isdir(path.join(path_, content)):
                    chdir(path_)
                    c += 1
                    try:
                        rmtree(content)
                        info('Removing Dir -> %s', content)
                    except Exception as er:
                        print 'Error: unable to remove dir -> %s' % er
                        error('unable to remove dir -> %s', er)
                    else:
                        dir_count += 1
                        print 'Cleaning From System -> %s' % content
                        debug('Cleaning From System -> %s', content)
                else:
                    chdir(path_)
                    c += 1
                    try:
                        unlink(content)
                        info('Removing File-> %s', content)
                    except Exception as er:
                        print 'Error: unable to remove file -> %s' % er
                        error('unable to remove file -> %s', er)
                    else:
                        file_count += 1
                        print 'Cleaning From System -> %s' % content
                        debug('Cleaning From System -> %s', content)
                total += 1
        print 'Summery'.center(40, '*')
        print 'Total files removed -> %s' % file_count
        debug('Total files removed -> %s', file_count)
        print 'Total dirs removed -> %s' % dir_count
        debug('Total dirs removed -> %s', dir_count)
        print 'Total removed -> %s' % total
        debug('Total removed -> %s', total)
        return file_count, dir_count, total


if __name__ == '__main__':
    trash_old_files_folders(path.abspath(TEMP_Path),
                            number_of_days=60)
    check_permissions_to_access_destination_artifacts(
        uri_for_permissions=destination_artifacts_url
    )
    #_synchronization_from_scr_to_destination()
    #_synchronization_for_deleted_items()
    #_synchronization_of_same_file_to_latest_one()
    _synchronization_of_same_file_to_latest_one()
