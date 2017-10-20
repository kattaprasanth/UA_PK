#!/usr/bin/env python

"""
Documentation :
This script was will perform Rsync between 2
JFrog ARTIFACTORY
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
from os import path, makedirs, unlink, stat, listdir, chdir, environ
from datetime import datetime
from time import time
from shutil import rmtree
from logging import info, error, warn, basicConfig, debug, DEBUG
from requests import get
from json import loads
from sys import exit, stdout

# User defined variables as needed
TEMP_PATH_ = 'C:\Users\Prasanth_Katta\Downloads\TEMP'
source_artifacts_url = 'http://35.198.202.31:8081/artifactory/PrasanthKatta'
destination_artifacts_url = 'http://35.198.202.31:8081/artifactory/Maven_Project_8'
source_artifacts_credentials = ('test', 'test123')
destination_artifacts_credentials = ('test', 'test123')

# TEMP and Logs path defined below
TEMP_PATH_DATE = 'TEMP_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
TEMP_Path = path.abspath(path.join(TEMP_PATH_, TEMP_PATH_DATE))
LOGS_PATH = path.abspath(path.join(TEMP_Path, 'logs'))
LOGS_PATH_FILE = path.abspath(
    path.join(LOGS_PATH, '%s'
              % (datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.log')))

# Create Required dirs and files as needed
if not path.exists(path.abspath(LOGS_PATH)):
    print "Creating Logs Dirs"
    stdout.flush()
    try:
        makedirs(path.abspath(LOGS_PATH))
    except Exception as e:
        print '[ERROR]: Unable to Create Logs Dir'
        print '[ERROR INFO]: %s' % e
        stdout.flush()

# Defined logs format and its path
if not path.exists(path.abspath(LOGS_PATH_FILE)):
    open(path.abspath(LOGS_PATH_FILE), 'w').close()
basicConfig(format=('%(asctime)s - %(levelname)s - %(message)s'),
            datefmt='%m/%d/%Y %I:%M:%S %p',
            filename='%s' % LOGS_PATH_FILE,
            level=DEBUG)

# connecting source
try:
    source_connect = ArtifactoryPath(source_artifacts_url,
                                     auth=source_artifacts_credentials)
except Exception as e:
    print '[ERROR]: Unable to connect to Source: %s' % source_artifacts_url
    print '[ERROR INFO]: %s' % e
    stdout.flush()
    error('Unable to connect to Source: %s' % source_artifacts_url)
    error(e)

# connecting destination
try:
    destination_connect = ArtifactoryPath(destination_artifacts_url,
                                          auth=destination_artifacts_credentials)
except Exception as e:
    print '[ERROR]: Unable to connect to destination: %s' % destination_artifacts_url
    print '[ERROR INFO]: %s' % e
    stdout.flush()
    error('Unable to connect to destination: %s' % destination_artifacts_url)
    error(e)

# Trying to get the max depth path and artifacts elinks
source_max_depth_Regex = compile(r'%s(.*)' % source_artifacts_url)
destination_max_depth_Regex = compile(r'%s(.*)' % destination_artifacts_url)


# checking users permission on destination side
def check_permissions_to_access_artifacts(uri_for_permissions=None):
    if uri_for_permissions:
        print 'Checking User Permissions in Progress..'.center(100, '=')
        print '[INFO] : Checking for User Permissions for the artifact'
        print '[INFO] : %s' % uri_for_permissions
        stdout.flush()
        info('Checking for User Permissions for the artifact')
        info(uri_for_permissions)
        repo_re = compile(r'(.*)artifactory/(.*)')
        try:
            repo = str(repo_re.search(uri_for_permissions).groups()[1]).split('/')[0]
        except Exception as ree:
            print '*'.center(60, '*')
            print '[ERROR]: Unable to get the permission on the given artifact repo key'
            print '%s' % ree
            print '*'.center(60, '*')
            stdout.flush()
            exit(1)
        if repo:
            print repo
            stdout.flush()
        else:
            print '[ERROR]: Unable to get the permission on the given artifact repo key'
            stdout.flush()
            exit(1)
        repo_uri = compile(r'(.*)artifactory')
        if repo_uri.search(uri_for_permissions).group():
            print 'check Repository permissions for artifact: %s' % repo_uri.search(uri_for_permissions).group()
            stdout.flush()
            info('check Repository permissions for artifact: %s' % repo_uri.search(uri_for_permissions).group())
            _uri_for_permission = repo_uri.search(uri_for_permissions).group() + \
                '/ui/artifactpermissions?repoKey=' + repo
            debug(_uri_for_permission)
            res = get(_uri_for_permission, auth=destination_artifacts_credentials)
            if res.status_code == 200:
                print 'Successfully connected to artifacts to check permissions'
                print _uri_for_permission
                stdout.flush()
                info('Successfully connected to artifacts to check permissions')
                debug(_uri_for_permission)
                try:
                    permission_data = loads(res.text)['userEffectivePermissions'][0]['permission']
                except ValueError as e:
                    print '*'.center(60, '*')
                    print '[ERROR]: Could not get the permission for the given destination'
                    print '%s' % e
                    print '*'.center(60, '*')
                    stdout.flush()
                    exit(1)
                debug(permission_data)
                if permission_data['read'] and permission_data['deploy']:
                    print 'User Have Read and Deploy permissions'
                    stdout.flush()
                    debug('User Have Read and Deploy permissions')
                else:
                    print '*'.center(60, '*')
                    print 'User Do not have permissions'
                    stdout.flush()
                    error('User Do not have permissions')
                    print '*'.center(60, '*')
                    exit(1)
                if permission_data['delete']:
                    print 'User Also has Delete Permissions to read and deploy'
                    stdout.flush()
                    debug('User Also has Delete Permissions to read and deploy')
                else:
                    print '*'.center(60, '*')
                    print 'User do not have permissions to delete'
                    error('User do not have permissions to delete')
                    print '*'.center(60, '*')
                    stdout.flush()
                    exit(1)


# gathering artifacts max depth of each link
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


# gathering only needed data from the raw data
def get_required_extended_links_only(artifact_full_link_data=None, regex_connect=None):
    filter_artifacts_data = set()
    if artifact_full_link_data and regex_connect:
        for each_link in artifact_full_link_data:
            filter_artifacts_data.add(regex_connect.search(each_link).groups()[0])
    return filter_artifacts_data


source_info = get_artifacts_full_data(uri=source_connect)
print 'Source artifacts information'.center(100, '#')
print list(source_info)
stdout.flush()
source_extended_info = get_required_extended_links_only(artifact_full_link_data=source_info,
                                                        regex_connect=source_max_depth_Regex)
debug(list(source_extended_info))
destination_info = get_artifacts_full_data(uri=destination_connect)
print 'Destination artifacts information'.center(100, '#')
print list(destination_info)
stdout.flush()
destination_extended_info = get_required_extended_links_only(artifact_full_link_data=destination_info,
                                                             regex_connect=destination_max_depth_Regex)
debug(list(destination_extended_info))


# gathering modified data and time for updated artifacts to push to destination
def get_artifacts_modified_date_and_time(uri=None, cred=None):
    if uri and cred:
        e_link = ArtifactoryPath(uri, auth=cred)
        artifact_modified_date = str(e_link.stat()[1]).split()[0]
        # print artifact_modified_date
        artifact_modified_time = str(e_link.stat()[1]).split()[1].split('+')[0].split('.')[0]
        # print artifact_modified_time
        if artifact_modified_date and artifact_modified_time:
            return artifact_modified_date, artifact_modified_time
        else:
            return exit(1)


# synchronization of same files on destination side if
# destination files date is less then source time stamp
def _synchronization_of_same_file_to_latest_one():
    same_artifacts_on_both = source_extended_info.intersection(destination_extended_info)
    if same_artifacts_on_both:
        print 'Synchronization of same artifacts in progress..'.center(100, '*')
        print '[INFO]: we have artifacts present on source and destination'
        stdout.flush()
        info('we have artifacts present on source and destination')
        print '[INFO]: checking they last modified time to sync again'
        stdout.flush()
        info('checking last modified time to sync with destination')
        print list(same_artifacts_on_both)
        stdout.flush()
        for each_modified_artifacts in same_artifacts_on_both:
            modified_source_uri = source_artifacts_url + each_modified_artifacts
            print modified_source_uri
            modified_destination_uri = destination_artifacts_url + each_modified_artifacts
            print modified_destination_uri
            print "collecting date and time of artifacts: %s".center(100, '=') % each_modified_artifacts
            stdout.flush()
            m_date_source, m_time_source = get_artifacts_modified_date_and_time(uri=modified_source_uri,
                                                                                cred=source_artifacts_credentials)
            m_date_des, m_time_des = get_artifacts_modified_date_and_time(uri=modified_destination_uri,
                                                                          cred=destination_artifacts_credentials)
            print "[INFO]: modified date: %s for source artifact: %s" % (m_date_source, each_modified_artifacts)
            info("modified date: %s for source artifact: %s" % (m_date_source, each_modified_artifacts))
            print "[INFO]: modified data: %s for destination artifact: %s" % (m_date_des, each_modified_artifacts)
            info("modified data: %s for destination artifact: %s" % (m_date_des, each_modified_artifacts))
            print "[INFO]: modified time: %s for source artifact: %s" % (m_time_source, each_modified_artifacts)
            info("modified time: %s for source artifact: %s" % (m_time_source, each_modified_artifacts))
            print "[INFO]: modified time: %s for destination artifact: %s" % (m_time_des, each_modified_artifacts)
            info("modified time: %s for destination artifact: %s" % (m_time_des, each_modified_artifacts))
            stdout.flush()
            if not m_date_des >= m_date_source:
                print '#'.center(60, '#')
                print '[INFO]: Below artifact needs to be updated on destination side'
                print '==> %s' % modified_destination_uri
                print '#'.center(60, '#')
                stdout.flush()
                modified_artifact_name = str(each_modified_artifacts).split('/')[-1]
                print modified_artifact_name
                modified_artifacts_path = str(each_modified_artifacts).split('/')[:-1]
                modified_artifacts_path_ = [mp for mp in modified_artifacts_path if mp]
                _download_path_ = path.abspath(path.join(TEMP_Path, 'modified_artifacts'))
                if modified_artifacts_path_:
                    modified_download_path = path.join(_download_path_, '/'.join(modified_artifacts_path_))
                    print "Creating local folder to download modified " \
                          "artifact from source" \
                          "%s" % path.abspath(modified_download_path)
                    stdout.flush()
                    debug('Creating local folder to download modified artifact from source')
                    debug("%s" % path.abspath(modified_download_path))
                    if not path.exists(path.abspath(modified_download_path)):
                        makedirs(path.abspath(modified_download_path))
                    __d_path = path.abspath(modified_download_path)
                else:
                    if not path.exists(path.abspath(_download_path_)):
                        makedirs(path.abspath(_download_path_))
                    __d_path = _download_path_
                debug(__d_path)
                print '#'.center(60, '#')
                print "Downloading Modified artifact form source " \
                      "%s" % modified_source_uri
                stdout.flush()
                debug("Downloading Modified artifact form source ")
                debug("%s" % modified_source_uri)
                print '#'.center(60, '#')
                m_artifacts_source = ArtifactoryPath(modified_source_uri, auth=source_artifacts_credentials)
                with m_artifacts_source.open() as fr:
                    with open(path.abspath(path.join(__d_path, modified_artifact_name)), 'wb') as out:
                        out.write(fr.read())
                if modified_artifacts_path_:
                    print '#'.center(60, '#')
                    print "Uploading Modified artifact to destination " \
                          "%s" % modified_destination_uri
                    print '#'.center(60, '#')
                    stdout.flush()
                    debug("Uploading Modified artifact to destination ")
                    debug("%s" % modified_destination_uri)
                    m_d_uri = destination_artifacts_url + '/' + '/'.join(modified_artifacts_path_)
                    print '==> %s' % m_d_uri
                    stdout.flush()
                    debug('==> %s' % m_d_uri)
                    m_artifact_des = ArtifactoryPath(m_d_uri, auth=destination_artifacts_credentials)
                else:
                    m_artifact_des = ArtifactoryPath(destination_artifacts_url, auth=destination_artifacts_credentials)
                m_artifact_des.deploy_file(path.abspath(path.join(__d_path, modified_artifact_name)))


# synchronization of artifacts if not present on destination
def _synchronization_from_scr_to_destination():
    print 'Synchronization of different artifacts in progress..'.center(100, '*')
    print 'synchronization from source: %s ' \
          'to destination: %s in progress ' % (source_artifacts_url, destination_artifacts_url)
    print '[INFO] : artifacts present in source and not in destination'
    stdout.flush()
    info('artifacts present in source and not in destination')
    source_but_not_destination = source_extended_info - destination_extended_info
    if source_but_not_destination:
        print list(source_but_not_destination)
        stdout.flush()
    else:
        print "[INFO] : Both Source and Destination are already in sync. No action required."
        stdout.flush()
        info("Both Source and Destination are already in sync. No action required.")
    for artifacts_not_in_destination in source_but_not_destination:
        main_source = source_artifacts_url + artifacts_not_in_destination
        _path = ArtifactoryPath(main_source, auth=source_artifacts_credentials)
        f_name = str(_path).split('/')[-1]
        info(f_name)
        f_full_path = [p for p in str(artifacts_not_in_destination).split('/')[:-1] if p]
        if f_full_path:
            print '/'.join(f_full_path)
            stdout.flush()
        if not path.exists(path.abspath(TEMP_Path)):
            try:
                makedirs(path.abspath(TEMP_Path))
            except Exception as dirs_errors:
                print '*'.center(60, '*')
                print '[ERROR]: Unable to Create dirs'
                print '[ERROR INFO]: %s' % dirs_errors
                print '*'.center(60, '*')
                stdout.flush()
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
                print '*'.center(60, '*')
                print '[ERROR]: Unable to create dirs'
                print '[ERROR INFO]: %s' % dirs_errors
                print '*'.center(60, '*')
                stdout.flush()
                error('Unable to create dirs')
                error(dirs_errors)
        print download_path
        print '#'.center(60, '#')
        print "Please wait. Downloading the artifacts: %s" % _path
        print '#'.center(60, '#')
        stdout.flush()
        debug("Please wait. Downloading the artifacts: %s" % _path)
        with _path.open() as fd:
            with open(path.abspath(path.join(download_path, f_name)), "wb") as out:
                out.write(fd.read())
        if f_full_path:
            change_new_path = destination_artifacts_url + '/' + '/'.join(f_full_path)
            print "Creating new path on destination Side: %s" % change_new_path
            stdout.flush()
            debug("Creating new path on destination Side: %s" % change_new_path)
            d_path = ArtifactoryPath(change_new_path, auth=destination_artifacts_credentials)
            if not d_path.exists():
                d_path.mkdir()
        else:
            d_path = ArtifactoryPath(destination_artifacts_url, auth=destination_artifacts_credentials)
        print '#'.center(60, '#')
        print "deploying the artifact to destination: %s" % d_path
        print '#'.center(60, '#')
        stdout.flush()
        debug("deploying the artifact to destination: %s" % d_path)
        d_path.deploy_file(path.abspath(path.join(download_path, f_name)))


# synchronization of artifacts for delete
# this function will unlink (only unlink artifact, it will not delete the complete path) the files from destination
# if those artifacts are removed from source
def _synchronization_for_deleted_items():
    print 'Synchronization of deleted artifacts in progress..'.center(100, '*')
    print 'artifacts present in destination: %s ' \
          'and not in source: %s' % (source_artifacts_url,
                                     destination_artifacts_url)
    stdout.flush()
    destination_but_not_source = destination_extended_info - source_extended_info
    if destination_but_not_source:
        print list(destination_but_not_source)
        stdout.flush()
        debug(list(destination_but_not_source))
    else:
        print "[INFO]: Both Source and destination are in sync. No deleting/removal required"
        stdout.flush()
        info('Both Source and destination are in sync. No deleting/removal required')
    if destination_but_not_source:
        for each_destination_deleted_artifact in destination_but_not_source:
            print '#'.center(60, '#')
            print "[INFO]: We have below artifact deleted from source."
            print "[INFO] : Deleting following artifact from destination " \
                  "as its removed from source " \
                  "artifacts : %s" % each_destination_deleted_artifact
            print '#'.center(60, '#')
            stdout.flush()
            debug('Deleting following artifact from destination')
            debug("artifacts : %s" % each_destination_deleted_artifact)
            destination_removal_url = destination_artifacts_url + each_destination_deleted_artifact
            print destination_removal_url
            stdout.flush()
            destination_removal_uri = ArtifactoryPath(destination_removal_url,
                                                      auth=destination_artifacts_credentials)
            if destination_removal_uri.is_dir():
                print "[INFO] : Removing destination dir tree"
                stdout.flush()
                debug('Removing destination dir tree')
                print '[INFO] : %s' % destination_removal_uri
                stdout.flush()
                debug('%s' % destination_removal_uri)
                destination_removal_uri.rmdir()
            elif destination_removal_uri.is_file():
                print "[INFO] : Removing destination artifact files"
                debug("Removing destination artifact files")
                print '[INFO] : %s' % destination_removal_uri
                stdout.flush()
                debug('%s' % destination_removal_uri)
                destination_removal_uri.unlink()
            else:
                print '[IMP INFO] : Some New type of file please add this'
                warn('[IMP INFO] : Some New type of file please add this')
                print '[IMP INFO] : %s' % destination_removal_uri
                warn('[IMP INFO] : %s' % destination_removal_uri)
                stdout.flush()


# trash old files and folder for the given path for the number of day old files
def trash_old_files_folders(path_=None, number_of_days=None):
    print "Trashing old data in progress..".center(100, '-')
    stdout.flush()
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
        stdout.flush()
        return file_count, dir_count, total


if __name__ == '__main__':
    trash_old_files_folders(path.abspath(TEMP_PATH_), number_of_days=1)
    check_permissions_to_access_artifacts(uri_for_permissions=destination_artifacts_url)
    _synchronization_from_scr_to_destination()
    _synchronization_of_same_file_to_latest_one()
    _synchronization_for_deleted_items()
