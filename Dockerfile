FROM cowrie/cowrie:latest

COPY ./cowrie-etc /cowrie/cowrie-git/etc
COPY ./cowrie-honeyfs /cowrie/cowrie-git/honeyfs
COPY ./cowrie-share /cowrie/cowrie-git/share/cowrie

