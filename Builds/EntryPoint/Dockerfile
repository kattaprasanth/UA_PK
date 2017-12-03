# This Docker File will create docker image which use ENTRYPOINT which runs all the time when container is used

FROM centos:latest
MAINTAINER Prasanth.Katta@gmail.com
RUN adduser -ms /bin/bash user
ENTRYPOINT echo "This Command will display this message on every container that is run from it"
USER user
