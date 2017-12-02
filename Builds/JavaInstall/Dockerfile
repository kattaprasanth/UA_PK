# This Docker File will install java and accepet the oracle license and install nettools and sets env vraibles like java_home and java_bin
# Pulling centos latest image from locally or from docker hub
FROM centos:latest
#Maintainer is the author
MAINTAINER Prasanth.Katta@gmail.com
# Adding user on base image
RUN adduser -ms /bin/bash user
# Adding properties as sudo user
RUN echo "EXPORT 192.168.100.0/24" >> /etc/exports.list
# udpated system to install required softwares also this operation is done as sudo user
RUN yum update -y
# Insatll net-tools and wegt s/w as required for below steps
RUN yum install -y net-tools wget
# Installing Oracle s/w with wget command and accepecting license as in the below command
RUN cd ~ && wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" \
"http://download.oracle.com/otn-pub/java/jdk/8u60-b27/jre-8u60-linux-x64.rpm"
#Belwo link experied
#"http://download.oracle.com/otn-pub/java/jdk/8u60-b27/jre-8u60-linux-x64.rpm"
# now we will install jre from local repo
RUN yum localinstall -y jre-8u60-linux-x64.rpm 
# Switching user
USER user
#From above user we will set env variables
RUN cd ~ && echo "export JAVA_HOME=/usr/java/jdk1.8.0_60/jre" >> /home/user/.bashrc
