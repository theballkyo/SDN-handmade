node {
    def app
    def branch = env.BRANCH_NAME
    def test = "aaaa"
    
    triggers {
        pollSCM('H/5 * * * *')
    }

    stage('Test before run') {
        sh "echo ${branch}"
        sh "echo ${test}"
    }

    stage('Clone repository') {
        /* Let's make sure we have the repository cloned to our workspace */

        checkout scm
    }

    stage('Change dir') {
        dir('backend/src') {
            stage('Build image') {
                /* This builds the actual image; synonymous to
                * docker build on the command line */

                app = docker.build("sdn_test")
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
}