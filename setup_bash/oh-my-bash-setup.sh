#!/bin/bash
#bash -c "$(curl -fsSL https://raw.githubusercontent.com/ohmybash/oh-my-bash/master/tools/install.sh)"
sed -i 's/OSH_THEME="font"/OSH_THEME="agnoster"/g' ~/.bashrc
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/local/istio-1.20.2/bin' >> ~/.bashrc
