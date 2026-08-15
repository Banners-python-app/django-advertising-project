pipeline {
    agent any
    options{
        skipDefaultCheckout(true)   // disable automatic checkout so we can control manually
        timestamps()        // show timestamps in console log, ensure plugin is installed
        disableConcurrentBuilds()
    }
    //parameters {
       // booleanParam(name: 'RUN_SLOW_TEST', defaultValue: false)
       // string(name: 'TARGET', defaultValue: 'local', description: 'Build target label')
    //}
    environment {
        PATH = "${WORKSPACE}/venv/bin:${env.PATH}"
        PIP_CACHE_DIR = "/tmp/jenkins-pip-cache/banners-pythonapp"  // pip will down here so we can reuse
        APP_NAME = 'banner-pythonapp'
        AWS_REGION = "us-east-1"
    }
    stages {
        stage ('Checking branch and Path') {
            steps {
                echo "Currently on BRANCH = ${env.BRANCH_NAME}"
                echo "With CHANGE_ID = ${env.CHANGE_ID}"
                echo "With PATH = ${env.PATH}"
            }
        }
        stage ('STAGE 1: Checkout & setup') {
            steps {
                checkout scm                // checkout scm

                sh '''
                    echo "Setting up Python Virt Env---------------------"
                    if [ ! -d "venv" ]; then 
                        python3 -m venv venv
                    fi 
                    mkdir -p $PIP_CACHE_DIR
                    pip install --upgrade pip
                    pip install --cache-dir $PIP_CACHE_DIR -r requirements.txt
                   ''' 
            }
        }
        stage ('STAGE 2: Secret Scanning(gitleaks)') {
            steps {
                script {
                    echo "Starting gitleaks scan for secret scanning--------------------"
                    // we use gitleaks official docker image, -v ${WORKSPACE}:/src mounts workspace into container
                    def scanResult = sh (
                        script: '''
                                docker run --rm -v ${WORKSPACE}:/src zricethezav/gitleaks:latest detect --source /src --verbose --redact
                                ''',
                                returnStatus: true      // capture exist code to provide the status
                    )
                    if (scanResult == 1) {
                        error("ALERT: Secret detected pls check logs...------------------")
                    } else if (scanResult != 0) {
                        error("ALERT: Gitleaks failed to run properly. Exit code ${scanResult}-------------")
                    } else {
                        echo "No secrets found. Code is clean!------------------"
                    }
                }
            }
        }
        stage ('STAGE 3: Linting') {
            steps {
                sh '''
                    pip install flake8
                    echo "Running strict syntax analysis..."
                    sleep 3
                    flake8 . --exclude=venv,.venv,env,.env --count --select=E9,F63,F72,F82 --show-source --statistics
                    echo "Running style and complexity checks..."
                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
                    '''
            }
        }
        stage ('STAGE 4: Unit test & code coverage') {
            environment {
                DEBUG = credentials('DEBUG')
                SECRET_KEY = credentials('SECRET_KEY')
                DATABASE_URL = credentials('DATABASE_URL')
                BLOB_READ_WRITE_TOKEN = credentials('BLOB_READ_WRITE_TOKEN')
                BLOB_STORE_ID = credentials('BLOB_STORE_ID')
            }
            steps {
                    // we alreay using pytest.ini file for xml report generation
                sh '''
                    sleep 3
                    pytest . --junitxml=reports/junit.xml
                   '''
            }
            post {
                always {
                    junit allowEmptyResults: false, testResults: 'reports/junit.xml'    // allowEmptyResults (if XML file missing or empty do not ignore it, crash the pipeline), testResults (junit refer this path for XML file)
                    archiveArtifacts artifacts: 'reports/**', fingerprint: true         // archiveArtifacts artifacts (grab entire report upload directly it to the Jenkins master server as permenant backup so it can be downloaded from UI), fingerprint (jenkins generate kryptographic MD5 file and track it for reuse or passed into other pipelines)
                }
            }
        }
        stage ('STAGE 5: Software composition analysis') {
            steps {
                script {
                    echo "Starting SCA...----------------"

                    def scaResult = sh (
                        script: '''
                                pip-audit -r requirements.txt --desc on -f columns
                                ''',
                                returnStatus: true
                    )
                    if (scaResult != 0) {
                        // unstable turns jenkins UI yellow but doent stop the pipeline
                        unstable("ALERT: Vulnerable dependencies found in requirements.txt! Please check...---------------")
                    } else {
                        echo "All depedencies are secure..!---------------------"
                    }
                }
            }
        }
        //stage ('STAGE 6: SonarQube Testing') {
          //  steps {
            //    script {
              //      echo "Starting SQ analysis----------------"

                //    def scannerHome = tool 'sonar-scanner'      // pulling the tool
                    
                    // 'sonarqube' needs to be match with Jenkins system setting
                  //  withSonarQubeEnv('sonarqube') {
                        // run the scanner 
                    //    sh "${scannerHome}/bin/sonar-scanner \
                      //      -Dsonar.projectKey=${env.APP_NAME} \
                        //    -Dsonar.sources=. \
                        //    -Dsonar.python.coverage.reportPaths=reports/coverage.xml \
                        //    -Dsonar.exclusions=venv/**,reports/**,**/*.pyc"
                    //}
                //}
            //}
        //}
        //stage ('Waiting for SonarQube') {
          //  steps {
            //    echo "Waiting for SQ to complete analysis----------------"

              //  timeout(time: 10, unit: 'MINUTES') {
               //     waitForQualityGate abortPipeline: true
              //  }
              //  echo "Quality gate passed! Code is secure---------------"
            //}
        //}
        stage ('STAGE 7: Building image') {
            environment { 
                AWS_AC_ID = "059325865650"
                ECR_REGISTRY = "${env.AWS_AC_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                REPO_NAME = "banners-pythonapp-repo"
            }
            steps {
                script {
                    echo "Building Docker image--------------"
                    // collecting git commit SHA
                    def gitCommit = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    // if TAG_NAME ? then take TAG_NAME else take GIT_COMMIT sha
                    def imageTag = env.TAG_NAME ? env.TAG_NAME : gitCommit

                    env.FULL_IMAGE_NAME = "${ECR_REGISTRY}/${env.REPO_NAME}:${imageTag}"

                    sh """
                        export DOCKER_BUILDKIT=1
                        docker build -t ${env.FULL_IMAGE_NAME} .
                        """
                }
            }
        }
        stage ('STAGE 8: Trivy Scan') {
            steps {
                script {
                    echo "Running Trivy scan against the build image--------------"
                    
                    // Ensure reports directory exists in workspace
                    sh "mkdir -p reports"

                    // 1. Generate human-readable text report
                    sh """
                        docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v ${WORKSPACE}/reports:/reports \
                        aquasec/trivy:latest image \
                        --format table \
                        --output /reports/trivy-report.txt \
                        --severity CRITICAL,HIGH \
                        --ignore-unfixed \
                        ${env.FULL_IMAGE_NAME}
                    """

                    // 2. Generate JSON report (standard for auditing / compliance logs)
                    sh """
                        docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v ${WORKSPACE}/reports:/reports \
                        aquasec/trivy:latest image \
                        --format json \
                        --output /reports/trivy-report.json \
                        --severity CRITICAL,HIGH \
                        --ignore-unfixed \
                        ${env.FULL_IMAGE_NAME}
                    """
                    // we are using docker.sock here which means trivy has root access of docker for security use ephemeral agents
                    def trivyResult = sh (
                        script: """
                            docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy:latest image \
                            --severity CRITICAL,HIGH \
                            --exit-code 1 \
                            --ignore-unfixed \
                            ${env.FULL_IMAGE_NAME}
                            """,
                            returnStatus: true
                    )

                    if (trivyResult != 0) {
                        unstable("ALERT: Critical or High issues found in image--------------")
                    } else {
                        echo "Docker image is secure-----------"
                    }
                }
            }
            post{
                always {
                    archiveArtifacts artifacts: 'reports/trivy-*.*', allowEmptyArchive: false
                }
            }
        }
    }
}