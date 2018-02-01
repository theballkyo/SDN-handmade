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
                    app = docker.build("registry.ryoka.tk/sdn_backend:latest")
                } else if (branch == 'master') {
                    app = docker.build("registry.ryoka.tk/sdn_backend:stable")
                } else {
                    app = docker.build("registry.ryoka.tk/sdn_backend:${branch}")
                }
            }

            stage('Test image') {
                configFileProvider([configFile(fileId: 'sdn-settings-test', targetLocation: 'settings.py')]) {
                    app.inside('-v $(pwd)/settings.py:/data/settings.py') {
                        sh 'python test_find_path.py'
                    }
                }
            }
        }
    }

    stage('Push docker image') {
        docker.withRegistry('https://registry.ryoka.tk', 'docker-registry') {
            // app.push("${env.BUILD_NUMBER}")
            app.push()
        }
    }
    
}