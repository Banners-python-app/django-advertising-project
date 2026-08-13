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
        PIP_CACHE_DIR = "/tmp/jenkins-pip-cache/${env.JOB_NAME}"  // pip will down here so we can reuse
        APP_NAME = 'banner-pythonapp'
        DEBUG = credentials('DEBUG')
        SECRET_KEY = credentials('SECRET_KEY')
        DATABASE_URL = credentials('DATABASE_URL')
        BLOB_READ_WRITE_TOKEN = credentials('BLOB_READ_WRITE_TOKEN')
        BLOB_STORE_ID = credentials('BLOB_STORE_ID')
    }
    stages {
        stage ('Checking branch and ') {
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
                    echo "Setting up Python Virt Env..."
                    sudo apt install python3.14-venv
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
                    echo "Starting gitleaks scan for secret scanning"
                    // we use gitleaks official docker image, -v ${WORKSPACE}:/src mounts workspace into container
                    def scanResult = sh (
                        script: '''
                                docker run --rm -v ${WORKSPACE}:/src zricethezav/gitleaks:latest detect --source /src --verbose --redact
                                ''',
                                returnStatus: true      // capture exist code to provide the status
                    )
                    if (scanResult == 1) {
                        error("ALERT: Secret detected pls check logs...")
                    } else if (scanResult != 0) {
                        error("ALERT: Gitleaks failed to run properly. Exit code ${scanResult}")
                    } else {
                        echo "No secrets found. Code is clean!"
                    }
                }
            }
        }
        stage ('STAGE 3: Linting') {
            steps {
                sh '''
                    pip install flake8
                    echo "Running strict syntax analysis..."
                    flake8 . --count --select=E9,F63,F72,F82 --show-source --statistics
                    echo "Running style and complexity checks..."
                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
                    '''
            }
        }
        stage ('STAGE 4: Unit test & code coverage') {
            steps {
                    // we alreay using pytest.ini file for xml report generation
                sh '''
                    pytest .
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
                    echo "Starting SCA..."

                    def scaResult = sh (
                        script: '''
                                pip install pip-audit
                                pip-audit -r requirements.txt --desc -f terminal
                                ''',
                                returnState: true
                    )
                    if (scaResult != 0) {
                        error("ALERT: Vulnerable dependencies found in requirements.txt! Please check...")
                    } else {
                        echo "All depedencies are secure..!"
                    }
                }
            }
        }
    }
}