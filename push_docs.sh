#!/bin/bash

echo -e "\033[0;32mDeploying updates to Github...\033[0m"

# Build the project.
cd docs
hugo
cd ..

# Add changes to git.
git add -A

# Commit changes.
msg="rebuilding site `date`"
if [ $# -eq 1 ]
    then msg="$1"
fi

git commit -m "$msg"

# Push source and build repos.
git push origin master
git subtree push --prefix=docs/public git@github.com:gliheng/blackhole.git gh-pages
