FROM alpine
RUN apk add py3-pip postgresql-client && pip3 install awscli
CMD pg_dump | gzip | aws s3 cp - s3://tdr-file-export/postgres-backup-$STAGE-`date +"%Y-%m-%d:%H:%M"`.gz

