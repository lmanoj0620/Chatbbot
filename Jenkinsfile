pipeline {
    agent any
    
    environment {
        AWS_ACCESS_KEY_ID     = credentials('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = credentials('AWS_SECRET_ACCESS_KEY')
        IMAGE_NAME   = "lmanojbalaji/manojbala:${GIT_COMMIT}"
        AWS_REGION   = "ap-south-1"
        CLUSTER_NAME = "demo-cluster"
        NAMESPACE    = "demo"
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
                sh "microk8s.kubectl apply -f Deployment.yaml"
            }
        }
    }
}
