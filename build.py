from shutit_module import ShutItModule

def build(shutit_session):
	# Installs
	shutit_session.send('apt -y -q install curl')

	# Repositories - golang
	shutit_session.send('add-apt-repository -y ppa:gophers/archive')
	shutit_session.send('echo "deb [arch=amd64] http://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list')
	# Repositories - bazel
	shutit_session.send('add-apt-repository -y ppa:gophers/archive')
	shutit_session.send('curl https://bazel.build/bazel-release.pub.gpg | apt-key add -')
	# Repositories - docker
	shutit_session.send('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -')
	shutit_session.send('add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"')
	shutit_session.send('add-apt-repository -y ppa:webupd8team/java')
	shutit_session.send('apt-get -y -q update')
	# golang, jdk and bazel, and docker. bazel - https://docs.bazel.build/versions/master/install-ubuntu.html#install-on-ubuntu
	shutit_session.send('apt-get -y -q install golang-1.10-go openjdk-8-jdk bazel python docker-ce build-essential make git apt-transport-https ca-certificates software-properties-common binutils-gold')
	shutit_session.send('apt-get upgrade -y -q bazel')

	# runc
	shutit_session.send('wget -qO- https://github.com/opencontainers/runc/releases/download/v1.0.0-rc5/runc.amd64 > /usr/local/bin/runc')
	shutit_session.send('chmod +x /usr/local/bin/runc')

	# gvisor	
	shutit_session.send('mkdir /usr/local/go')
	shutit_session.send('export GOPATH=/usr/local/go')
	shutit_session.send('git clone https://gvisor.googlesource.com/gvisor gvisor')
	shutit_session.send('cd gvisor')
	shutit_session.send('bazel build runsc')
	shutit_session.send('cp ./bazel-bin/runsc/linux_amd64_pure_stripped/runsc /usr/local/bin')

	# Reconfigure docker to make network work, and use runsc
	shutit_session.insert_text('Environment=GODEBUG=netdns=cgo','/lib/systemd/system/docker.service',pattern='.Service.')
	shutit_session.send('mkdir -p /etc/docker',note='Create the docker config folder')
	shutit_session.send_file('/etc/docker/daemon.json',"""{
	"dns": ["8.8.8.8"],
	"runtimes": {
		"runsc": {
			"path": "/usr/local/bin/runsc",
			"runtimeArgs": [
				"--debug-log-dir=/tmp/runsc",
				"--debug",
				"--strace",
				"--log-packets"
			]
		}
	}
}""")
	shutit_session.send('systemctl daemon-reload')
	shutit_session.send('systemctl restart docker')

	# Run containers
	shutit_session.send('docker run --runtime=runsc hello-world')
	# Bug here - see https://github.com/google/gvisor/issues/37
	#shutit_session.send('docker run -d --runtime=runsc --name gvisor -it ubuntu sleep 9999')
	#shutit_session.login('docker exec -ti gvisor bash')
	#shutit_session.logout()
	shutit_session.pause_point('see files under /tmp/runsc')
