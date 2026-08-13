This is guide for building your Jenkinsfile n pipeline.
1. Create new Multibranch pipeline job, Under Branch source add ur github repo and credentials. 
    In Discover Branches select "Only brnaches that are files as PRs"
    In Discover pull requests from origin select Merging the pull request with the current target branch revision.
    In Discover pull requests from forks selects same as above
    Now use Filter - Filter by name add this ^(dev|main|PR-.*)$ 
    