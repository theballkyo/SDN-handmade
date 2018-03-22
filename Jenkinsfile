node {
    def app
    def branch = env.BRANCH_NAME
    def test = "aaaa"
    def mydata

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
                    app = docker.build("registry.docker.ryoka.tk/sdn_backend:latest")
                } else if (branch == 'master') {
                    app = docker.build("registry.docker.ryoka.tk/sdn_backend:stable")
                } else {
                    app = docker.build("registry.docker.ryoka.tk/sdn_backend:${branch}")
                }
            }

            stage('Test image') {
                configFileProvider([configFile(fileId: 'sdn-settings-test', targetLocation: 'settings.py', variable: 'SDN_SETTINGS')]) {
                    mydata = readFile encoding: 'utf-8', file: 'settings.py'
                    app.inside('--network db') {
                        sh "echo ${mydata} | base64 --decode > settings.py"
                        echo "Testing settings file"
                        sh 'cat settings.py'
                        sh 'export PYTHONPATH=$(pwd) && python tests/test_find_path.py'
                    }
                }
            }
        }
    }

    stage('Push docker image') {
        if (branch == 'develop') {
            docker.withRegistry('https://registry.docker.ryoka.tk', 'docker-registry') {
                app.push("develop")
            }
        } else if (branch == 'master') {
            docker.withRegistry('https://registry.docker.ryoka.tk', 'docker-registry') {
                app.push()
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
    
}