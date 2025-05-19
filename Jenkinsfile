pipeline {
  agent any

  environment {
    PROJECT_NAME = "fastapi_ci"
    COMPOSE_FILE = "docker-compose.yml"
  }

  stages {
    stage('Checkout') {
      steps {
        git url: 'https://github.com/your-username/your-repo.git', branch: 'main'
      }
    }
    stage('Build & Deploy') {
      steps {
        sh "docker-compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} down || true"
        sh "docker-compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} up --build -d"
      }
    }
  }

  post {
    always {
      sh "docker system prune -f"
    }
  }
}

