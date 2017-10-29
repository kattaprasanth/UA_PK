#!/bin/bash

d=`date +%Y-%m-%d`
commit_name="Excrcise $d"
echo "$commit_name"

echo "Adding latest changed files to git"

git add -A

echo "Adding Commit Messages to the changes"

git commit -m "$commit_name"

echo "Pushing Changes to Git"

git push
