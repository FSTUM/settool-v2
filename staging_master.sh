#!/bin/sh
while true; do 
  git fetch origin
  reslog=$(git log HEAD..origin/main --oneline)
  if [ "${reslog}" != "" ] ; then
    git merge origin/master # completing the pull
    echo "last Run:"
    date
    sh staging.sh
  fi
  sleep 1m
done
