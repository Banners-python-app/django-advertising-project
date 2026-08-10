pipeline {
    agent any
    options{
        //timestamps()
        disableConcurrentBuilds()
    }
    parameters{
        booleanParam(name: 'RUN_SLOW_TEST', defaultValue: false)
        string(name: 'TARGET', defaultValue: 'local', description: 'Build target label')
    }
    environment {
        APP_NAME = 'banner-pythonapp'
    }
    stages {
        stage ('Checkout info') {
            steps {
                echo "Building ${env.APP_NAME} for TARGET=${params.TARGET}"
                // fetch commit SHA | add to commi.tx ||(OR) run only if earlier cmd failed
                sh 'git rev-parse --short HEAD | tee commit.txt || echo "no-git-in-commit" | tee commit.txt'
                sh 'ls -la'
            }
        }
        stage ('Test') {
            steps {
                sh 'test -f Jenkinsfile'
                sh 'test -f readme.md'
            }
        }
        stage('Slow Test') {
            when{
                expression { params.RUN_SLOW_TEST }
            }
            steps {
                echo "Slow tests"
            }
        }
    }
    post{
        always {
            echo "SCM Pipeline finished: ${currentBuild.currentResult}"
        }
    }
}