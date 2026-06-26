pipeline {
    agent any
    
    environment {
        IMAGE_NAME   = "lmanojbalaji/manojbala:${GIT_COMMIT}"
    }

    stages {

        stage('Git-checkout') {
            steps {
                git url: 'https://github.com/lmanoj0620/Chatbbot.git', branch: 'main'
            }
        }

        stage('Building-Stage') {
            steps {
                sh '''
                    printenv
                    docker build -t ${IMAGE_NAME} .
                '''
            }
        }

        stage('Login to Docker Hub') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'docker-hub-creds',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {
                    sh 'echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin'
                }
            }
        }

        stage('Pushing to Docker hub') {
            steps {
                sh '''
                    docker push ${IMAGE_NAME}
                '''
            }
        }
        stage("Deploy to microk8s") {
            steps {
                sh "sed -i 's|replace|${IMAGE_NAME}|g' Deployment.yaml"
                sh "microk8s.kubectl apply -f Deployment.yaml"
            }
        }
    }
}
