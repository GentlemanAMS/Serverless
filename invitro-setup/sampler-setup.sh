#!/bin/bash

INVITRO_REPO=$HOME/invitro

AZURE_TRACE_LOCATION=$INVITRO_REPO/data/azure/
SAMPLED_TRACE_LOCATION=$INVITRO_REPO/data/traces/reference

cd $INVITRO_REPO
sudo apt update
sudo apt -y install git-lfs pip xz-utils
git lfs install

cd $INVITRO_REPO/sampler
git lfs fetch
git lfs checkout
pip install -r $INVITRO_REPO/requirements.txt

# Deleting all previous files
rm -rf $AZURE_TRACE_LOCATION
rm -rf $SAMPLED_TRACE_LOCATION

# Creating new folders
mkdir -p $AZURE_TRACE_LOCATION
mkdir -p $SAMPLED_TRACE_LOCATION 

# Download the azure trace
wget https://azurecloudpublicdataset2.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2019/azurefunctions-dataset2019.tar.xz -P $AZURE_TRACE_LOCATION
tar -xf $AZURE_TRACE_LOCATION/azurefunctions-dataset2019.tar.xz -C $AZURE_TRACE_LOCATION

# Preprocess the trace
cd $INVITRO_REPO
python3 -m sampler preprocess -t $AZURE_TRACE_LOCATION -o $SAMPLED_TRACE_LOCATION/preprocessed_150 -s 00:09:00 -dur 150

# Sample the trace
cd $INVITRO_REPO
python3 -m sampler sample -t $SAMPLED_TRACE_LOCATION/preprocessed_150 -orig $SAMPLED_TRACE_LOCATION/preprocessed_150 -o $SAMPLED_TRACE_LOCATION/sampled_150 -min 3000 -st 1000 -max 24000 -tr 16

cd $INVITRO_REPO
python3 -m sampler sample -t $SAMPLED_TRACE_LOCATION/sampled_150/samples/3000 -orig $SAMPLED_TRACE_LOCATION/preprocessed_150 -o $SAMPLED_TRACE_LOCATION/sampled_150 -min 200 -st 50 -max 3000 -tr 16

cd $INVITRO_REPO
python3 -m sampler sample -t $SAMPLED_TRACE_LOCATION/sampled_150/samples/200 -orig $SAMPLED_TRACE_LOCATION/preprocessed_150 -o $SAMPLED_TRACE_LOCATION/sampled_150 -min 10 -st 10 -max 200 -tr 16

 

