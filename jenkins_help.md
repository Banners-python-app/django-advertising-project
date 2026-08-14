This is guide for building your Jenkinsfile n pipeline.
1. Create new Multibranch pipeline job, Under Branch source add ur github repo and credentials. 
    In Discover Branches select "Only brnaches that are files as PRs"
    In Discover pull requests from origin select Merging the pull request with the current target branch revision.
    In Discover pull requests from forks selects same as above
    Now use Filter - Filter by name add this ^(dev|main|PR-.*)$ 
2. On GH repo/ org create strict branch rules for PR on dev and main branch.
3. Create Github app select permissions: Checks, Commit status, COntent read-only, Pull requests read.
    In account permission select Events read-only.