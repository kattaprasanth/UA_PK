# This Image is based on centos7 and will start apache on each container

FROM centos:latest
MAINTAINER Prasanth.Katta@gmail.com

RUN yum update -y
RUN yum install -y httpd net-tools
RUN echo "This is a custome index file build during the image creation" > /var/www/html/index.html

EXPOSE 80
ENTRYPOINT apachectl "-DFOREGROUND"
