#!/bin/bash

# clone vHive repository in home directory
cd $HOME
git clone --depth=1 https://github.com/vhive-serverless/vhive.git
echo "vHive repository cloned\n"

# Create directory for vHive logs
mkdir -p /tmp/vhive-logs/

# Change your working directory to the root of the repository
cd vhive






# Delete previous go if already installed
sudo rm -rf /usr/local/go

VERSION=1.21.4        # Go version to be installed
ARCH=amd64          # Arcihitecture
if [ $(uname -i) == "aarch64" ]; then ARCH=arm64 ; fi

GO_BUILD="go${VERSION}.linux-${ARCH}"  # tar file from which go has to be built
echo "==> Install: Go ${VERSION} for ${ARCH}"

# Get the go tar file
wget --continue --quiet https://golang.org/dl/${GO_BUILD}.tar.gz

# Unzip and install the binaries at /usr/local
sudo tar -C /usr/local -xzf ${GO_BUILD}.tar.gz

# Export the paths
export PATH=$PATH:/usr/local/go/bin
sudo sh -c  "echo 'export PATH=\$PATH:/usr/local/go/bin' >> /etc/profile"
sh -c  "echo 'export PATH=\$PATH:/usr/local/go/bin' >> $HOME/.bashrc"
source /etc/profile

echo "Installed: $(go version)"





# Install protoc
PB_VERSION=25.0

# Download the protoc from the below website
PB_REL="https://github.com/protocolbuffers/protobuf/releases"
curl -LO $PB_REL/download/v$PB_VERSION/protoc-$PB_VERSION-linux-x86_64.zip

# Install the protoc at ~/.local
unzip protoc-$PB_VERSION-linux-x86_64.zip -d $HOME/.local

# Exporting the paths
sh -c "echo 'export PATH=\$PATH:\$HOME/.local/bin' >> $HOME/.bashrc"
export PATH="$PATH:$HOME/.local/bin"

# Install go : protoc-gen-go, protoc-gen-go-grpc
go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.31
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.3

# Exporting the paths
sh -c "echo 'export PATH=\$PATH:\$(go env GOPATH)/bin' >> $HOME/.bashrc"
export PATH="$PATH:$(go env GOPATH)/bin"




# clone vSwarm repository
# cd $HOME
# git clone git@github.com:vhive-serverless/vSwarm.git
# echo "vSwarm repository cloned"


# Build the setup tool
cd $HOME/vhive
pushd scripts && go build -o setup_tool && popd && mv scripts/setup_tool .
echo "vHive setup tool built"
cd $HOME/vhive
