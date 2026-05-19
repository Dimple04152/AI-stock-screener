pipeline {
    agent any

    environment {
        DOCKER_HUB_USER = "bitslasher1003"
        KUBECONFIG_CREDENTIAL_ID = "k8s-kubeconfig"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/adityaMachal/AI-stock-screener.git'
            }
        }

        stage('Build & Push Images') {
            steps {
                script {
                    docker.withRegistry('', 'docker-hub-credentials') {
                        // Backend
                        def backendImg = docker.build("${DOCKER_HUB_USER}/stock-backend:${env.BUILD_NUMBER}", "-f Dockerfile.backend .")
                        backendImg.push()
                        backendImg.push("latest")

                        // Frontend
                        def frontendImg = docker.build("${DOCKER_HUB_USER}/stock-frontend:${env.BUILD_NUMBER}", "-f Dockerfile.frontend .")
                        frontendImg.push()
                        frontendImg.push("latest")

                        // LLM Service
                        def llmImg = docker.build("${DOCKER_HUB_USER}/stock-llm-service:${env.BUILD_NUMBER}", "services/llm_service")
                        llmImg.push()
                        llmImg.push("latest")

                        // Sync Worker
                        def syncImg = docker.build("${DOCKER_HUB_USER}/stock-sync-worker:${env.BUILD_NUMBER}", "services/data_sync_worker")
                        syncImg.push()
                        syncImg.push("latest")
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            agent {
                docker {
                    image 'bitnami/kubectl:latest'
                    args '-u 0'
                }
            }
            steps {
                withKubeConfig([credentialsId: KUBECONFIG_CREDENTIAL_ID]) {
                    sh "kubectl apply -f k8s/"
                    // Force rollout to pick up new images if using 'latest' tag
                    sh "kubectl rollout restart deployment/stock-backend"
                    sh "kubectl rollout restart deployment/stock-frontend"
                    sh "kubectl rollout restart deployment/llm-service"
                    sh "kubectl rollout restart deployment/sync-worker"
                }
            }
        }
    }
}
