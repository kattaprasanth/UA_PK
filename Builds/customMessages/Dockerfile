# This Docker File will create docker images as non-privilaged user

FROM centos:latest
MAINTAINER Prasanth.Katta@gmail.com
RUN adduser -ms /bin/bash user
RUN echo "EXPORT 192.168.100.0/24" >> /etc/exports.list
USER user
