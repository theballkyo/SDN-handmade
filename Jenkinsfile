node {
    def app
    def branch = env.BRANCH_NAME
    def test = "aaaa"

    stage('Test before run') {
        sh "echo ${branch}"
        sh "echo ${test}"
    }

    stage('Clone repository') {
        /* Let's make sure we have the repository cloned to our workspace */

        checkout scm
    }

    stage('Change dir to backend') {
        dir('backend/src') {
            stage('Build image') {
                /* This builds the actual image; synonymous to
                * docker build on the command line */
                if (branch == 'develop') {
                    app = docker.build("sdn_backend:latest")
                } else if (branch == 'master') {
                    app = docker.build("sdn_backend:stable")
                } else {
                    app = docker.build("sdn_backend:${branch}")
                }
            }

            stage('Test image') {
                /* Ideally, we would run a test framework against our image.
                * For this example, we're using a Volkswagen-type approach ;-) */

                app.inside {
                    sh 'echo "Tests passed"'
                }
            }
        }
    }

    stage('Push image') {
        sh 'echo "Todo ja"'
    }
}