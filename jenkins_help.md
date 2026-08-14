This is guide for building your Jenkinsfile n pipeline.
1. Create new Multibranch pipeline job, Under Branch source add ur github repo and credentials. 
    In Discover Branches select "Only brnaches that are files as PRs"
    In Discover pull requests from origin select Merging the pull request with the current target branch revision.
    In Discover pull requests from forks selects same as above
    Now use Filter - Filter by name add this ^(dev|main|PR-.*)$ 
2. On GH repo/ org create strict branch rules for PR on dev and main branch.
3. Create Github app select permissions: Checks, Commit status, COntent read-only, Pull requests read.
    In account permission select Events read-only.
4. See the pipeline for for the stages.
5. Coming to SAST SonarQube stage we have plugin Sonarqube we can install it.
    Now on Sonarqube server run this cmd #sysctl -w vm.max_map_count=262144 (SQ runs elasticsearch under the hood to index your code. ES required host operating system to allow massive amount of memory mapping.)
    Create 1 more EC2 with c7i.xlarge instance type and use docker-compose file. 
    Then login to Sonarqube UI generate a token from security tab in Accounts option. Store the token in Jnekins cred manager.
    After got System -> Sonarqube server -> Check the checkbox for Env vars and fill the server info.
    Now in SQ UI go to Administration -> COnfiguration -> Webhooks  http://ip:8080/jenkins-webhook/