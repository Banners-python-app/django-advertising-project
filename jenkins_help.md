This is guide for building your Jenkinsfile n pipeline.
1. Create new Multibranch pipeline job, Under Branch source add ur github repo and credentials. 
    In Discover Branches select "All branches"
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
    Now in Jenkins -> tools -> Setup Sonar scanner -> install automatically
    After got System -> Sonarqube server -> Check the checkbox for Env vars and fill the server info.
    Now in SQ UI go to Administration -> Cnfiguration -> Webhooks  http://ip:8080/jenkins-webhook/
    Build the pipeline given in Jfile.
6. Now we need to build the image and tag it with git tag version, lets see first settings in Jenkins.
    Open Multibranch pipeline -> Configure -> Under Branch Sources -> Behaviours -> Add -> Doscover Tags -> Save. 
    Now create a role instance profile in AWS & attach AmazonEC2ContainerRegistryPowerUser policies to it. Attach same role to EC2. This will help to push/pull images to ECR.
    Now prepare the pipeline.
7. Now for trivy image scan enterprise uses docker trivy image using below cmd or they install trivy on nodes. But using docker image uses docker.sock bcaz trivy is in container and dontianer needs to contact other container and this will give a root docker access to trivy.
Way to handle this is using ephemeral agents like kubernetes/docker, use trusted image only or use native trivy installation on nodes.