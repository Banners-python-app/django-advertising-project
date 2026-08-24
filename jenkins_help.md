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

==================================================
ArgoCD immediate repo sync steps:-
By default, ArgoCD operates on a "pull" model, polling your GitHub repository every 3 minutes to check for changes.

To achieve instant syncs, real enterprises bypass this 3-minute delay by configuring GitHub Webhooks. When a webhook is configured, GitHub instantly sends an HTTP POST request to ArgoCD the millisecond a merge or push occurs, triggering an immediate sync.

Here is exactly how to set this up using enterprise security standards (which require a webhook secret so random bots cannot trigger your deployments).

Step 1: Create a Webhook Secret Token
You need a cryptographic secret so ArgoCD knows the webhook is genuinely coming from GitHub.
Generate a random string on your terminal:

Bash
ruby -rsecurerandom -e 'puts SecureRandom.hex(20)'
# Example output: a1b2c3d4e5f6g7h8i9j0
Save this token; you will need it in the next two steps.

Step 2: Configure ArgoCD to Trust the Token
You must store this token in ArgoCD's core Kubernetes secret so it can validate GitHub's incoming requests.

Run this command to patch the argocd-secret in your cluster, replacing YOUR_TOKEN_HERE with the token you just generated:

Bash
kubectl patch secret argocd-secret -n argocd \
  -p '{"stringData": {"webhook.github.secret": "YOUR_TOKEN_HERE"}}'
Note: If you are using External Secrets Operator to manage ArgoCD's secrets, add this key-value pair to AWS Secrets Manager instead.

Step 3: Configure the Webhook in GitHub
Now, tell GitHub where to send the instant notifications.

Go to your GitHub repository (or GitHub Organization) -> Settings -> Webhooks.

Click Add webhook.

Fill in the following details:

Payload URL: [https://argocd.yourcompany.com/api/webhook](https://argocd.yourcompany.com/api/webhook) (must include the /api/webhook path)

Content type: application/json

Secret: Paste your token from Step 1.

Which events would you like to trigger this webhook? Select "Just the push event."

Click Add webhook.

How it works in production
The next time a developer merges a Pull Request to the main branch, GitHub calculates a SHA256 hash using your secret token and sends it alongside the push data to ArgoCD. ArgoCD verifies the hash, identifies which Application tracks that specific Git path, and instantly begins the deployment without waiting for the 3-minute polling cycle.