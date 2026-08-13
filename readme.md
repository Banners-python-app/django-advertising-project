1. In Dockerfile we are using buildkit and buildx so we need to install extra packages as mentioned in the Dockerfile RUN and also install buildx. For buildkit we need to enable it.
2. As we are using Jenkins foe CI-CD lets do some settings.
    1. Create GitHub app in account or in organizations
    2. Install Jenkins on EC2 or use labs, etc
    3. In Jenkins plugins install GitHub Branch Source, Github.

Jenkinsfile stages:
Stage 1: Checkout & Setup
The Goal: Pull the code and set up the working environment.

The Hint: Use the standard Jenkins checkout scm step. For a Python environment, your hint is to set up a Python Virtual Environment (venv) in your workspace during this step so that all subsequent pip install commands are isolated and don't conflict with the Jenkins server's system Python.

Stage 2: Secret Scanning (Gitleaks)
The Goal: Ensure no developer accidentally hardcoded an AWS key, database password, or API token into the Django settings.py or other files.

The Hint: You don't need a heavy Jenkins plugin for this. The enterprise standard is to run the official Gitleaks Docker container inside your Jenkins sh step, mounting your current workspace as a volume to scan it. If it finds a secret, it returns a non-zero exit code and fails the pipeline instantly.

Stage 3: Linting & Code Quality
The Goal: Enforce standard Python formatting (PEP 8) so the codebase remains readable and uniform.

The Hint: Inside your virtual environment, install flake8 and black. Run them against your Django app directory. You can configure them to just warn, but in production, teams configure this stage to fail if the code is improperly formatted.

Stage 4: Unit Testing & Code Coverage
The Goal: Prove the application logic works and ensure enough of the code is actually being tested.

The Hint: Use pytest along with pytest-django and pytest-cov.

Pro-hint: Output the test results as an XML file. You can then use the Jenkins JUnit Plugin to read that XML and generate a beautiful test trend graph directly on your Jenkins job dashboard.

Stage 5: SCA (Software Composition Analysis)
The Goal: Django apps rely heavily on requirements.txt. SCA checks if any of those third-party libraries have known public vulnerabilities (CVEs).

The Hint: Use a tool called safety (a Python dependency vulnerability scanner) or pip-audit. You run this via a simple shell command against your requirements file. If it finds a critical CVE in a package like Django or Pillow, it breaks the build.

Stage 6: SAST (Static Application Security Testing)
The Goal: Scan your actual proprietary code for security flaws (like SQL injection risks, cross-site scripting, or unsafe YAML parsing).

The Hint: For Python, the industry standard open-source tool is Bandit. Run bandit -r . in your shell step.

Enterprise Hint: Many large companies also use SonarQube here, which has a dedicated Jenkins plugin and sends the scan results to a centralized SonarQube dashboard for management to review.

Stage 7: Container Image Build
The Goal: Package the Django app and its dependencies into an immutable Docker image.

The Hint: Use the Jenkins sh step to run standard docker build -t your-app-name:$BUILD_NUMBER .. Tagging it with the Jenkins $BUILD_NUMBER ensures every image has a unique, traceable ID.

Stage 8: Container Vulnerability Scan
The Goal: Now that the OS packages and Python app are bundled into a Docker image, scan the entire image layer by layer for OS-level vulnerabilities (like OpenSSL bugs).

The Hint: Use an open-source tool called Trivy. You can run trivy image your-app-name:$BUILD_NUMBER. Trivy will scan the local image you just built in Stage 7 and fail the build if it detects "CRITICAL" vulnerabilities before the image is allowed to leave the server.

Stage 9: Push to Registry & Cleanup
The Goal: Send the verified, secure image to a container registry (like AWS ECR, Docker Hub, or Harbor) so Kubernetes can pull it for deployment.

The Hint: Use the Jenkins withCredentials block to securely log into your Docker registry, run docker push, and then—crucially—run docker rmi to delete the image off the Jenkins worker node so your server doesn't run out of disk space.