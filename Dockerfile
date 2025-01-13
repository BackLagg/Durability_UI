FROM ubuntu:latest
LABEL authors="shahn"

ENTRYPOINT ["top", "-b"]