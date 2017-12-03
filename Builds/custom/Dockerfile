# This Docker file will use centos and install openssh and apache server also open ports for 22 and 80

FROM centos:latest
MAINTAINER PrasanthKatta<Prasanth.Katta@gmail.com>

RUN yum update -y
RUN yum install -y net-tools httpd

EXPOSE 80 22

ENTRYPOINT apachectl "-DFOREGROUND"


