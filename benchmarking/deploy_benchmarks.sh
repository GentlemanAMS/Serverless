#!/bin/bash

# Following benchmarks can be deployed and invoked
DEPLOY_AES=1
DEPLOY_AUTH=0
DEPLOY_CHAINED_FUNCTION_SERVING=0
DEPLOY_FIBONACCI=0
DEPLOY_GPTG=0
DEPLOY_ONLINE_SHOP=0
DEPLOY_VIDEO_ANALYTICS=0


# Following benchmarks can be deployed but some functions of these benchmarks face some issue when invoked
DEPLOY_BERT=0
DEPLOY_HOTEL_APP=0

# Following benchmarks cannot be deployed
# These do not seem to work because I think they require AWS S3 Secret keys and stuffs like that
DEPLOY_CHAINED_FUNCTION_EVENTING=0
DEPLOY_CORRAL=0
DEPLOY_GG=0
DEPLOY_MAP_REDUCE=0
DEPLOY_STACKING_TRAINING=0
DEPLOY_TUNING_HALVING=0

echo "Following Benchmarks Cannot be Deployed"
echo "-) Chained Function Eventing"
echo "-) Corral"
echo "-) GG"
echo "-) Map Reduce"
echo "-) Stacking Training"
echo "-) Tuning Halving"

BENCHMARKS="$HOME/vSwarm/benchmarks"
DEPLOYER_SCRIPT="$HOME/vSwarm/tools/kn_deploy.sh"

benchmarks_deployed=()

if [ "$DEPLOY_AES" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/aes/yamls/knative/kn-aes-go-tracing.yaml
        kubectl apply -f $BENCHMARKS/aes/yamls/knative/kn-aes-go.yaml
        kubectl apply -f $BENCHMARKS/aes/yamls/knative/kn-aes-nodejs-tracing.yaml
        kubectl apply -f $BENCHMARKS/aes/yamls/knative/kn-aes-nodejs.yaml
        kubectl apply -f $BENCHMARKS/aes/yamls/knative/kn-aes-python-tracing.yaml
        kubectl apply -f $BENCHMARKS/aes/yamls/knative/kn-aes-python.yaml
        benchmarks_deployed+=("AES")
fi

if [ "$DEPLOY_AUTH" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/auth/yamls/knative/kn-auth-go-tracing.yaml
        kubectl apply -f $BENCHMARKS/auth/yamls/knative/kn-auth-go.yaml
        kubectl apply -f $BENCHMARKS/auth/yamls/knative/kn-auth-nodejs-tracing.yaml
        kubectl apply -f $BENCHMARKS/auth/yamls/knative/kn-auth-nodejs.yaml
        kubectl apply -f $BENCHMARKS/auth/yamls/knative/kn-auth-python-tracing.yaml
        kubectl apply -f $BENCHMARKS/auth/yamls/knative/kn-auth-python.yaml
        benchmarks_deployed+=("AUTH")
fi

if [ "$DEPLOY_BERT" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/bert/yamls/knative/kn-bert-python.yaml
        benchmarks_deployed+=("BERT")
fi

if [ "$DEPLOY_CHAINED_FUNCTION_SERVING" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/chained-function-serving/yamls/knative/inline/service-consumer.yaml
        kubectl apply -f $BENCHMARKS/chained-function-serving/yamls/knative/inline/service-driver.yaml
        kubectl apply -f $BENCHMARKS/chained-function-serving/yamls/knative/inline/service-producer.yaml
        benchmarks_deployed+=("CHAINED FUNCTION SERVING")
fi

if [ "$DEPLOY_FIBONACCI" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/fibonacci/yamls/knative/kn-fibonacci-go-tracing.yaml
        kubectl apply -f $BENCHMARKS/fibonacci/yamls/knative/kn-fibonacci-go.yaml
        kubectl apply -f $BENCHMARKS/fibonacci/yamls/knative/kn-fibonacci-nodejs-tracing.yaml
        kubectl apply -f $BENCHMARKS/fibonacci/yamls/knative/kn-fibonacci-nodejs.yaml
        kubectl apply -f $BENCHMARKS/fibonacci/yamls/knative/kn-fibonacci-python-tracing.yaml
        kubectl apply -f $BENCHMARKS/fibonacci/yamls/knative/kn-fibonacci-python.yaml
        benchmarks_deployed+=("FIBONACCI")
fi

if [ "$DEPLOY_GPTG" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/gptj/yamls/knative/kn-gptj-python.yaml
        benchmarks_deployed+=("GPTG")
fi

if [ "$DEPLOY_HOTEL_APP" -eq 1 ]; then
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/database.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/memcached.yaml
        kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-geo-tracing.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-geo.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-profile.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-rate.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-recommendation.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-reservation.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-search-tracing.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-search.yaml
	kubectl apply -f $BENCHMARKS/hotel-app/yamls/knative/kn-user.yaml
        benchmarks_deployed+=("HOTEL APP")
fi

if [ "$DEPLOY_ONLINE_SHOP" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/database.yaml
	kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-adservice.yaml
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-cartservice.yaml
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-currencyservice.yaml
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-emailservice.yaml
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-paymentservice.yaml
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-productcatalogservice.yaml
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-recommendationservice.yaml
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-shippingservice.yaml
        kubectl apply -f $BENCHMARKS/online-shop/yamls/knative/kn-checkoutservice.yaml
	benchmarks_deployed+=("ONLINE SHOP")
fi

# This does not work because AWS secret keys are required
if [ "$DEPLOY_TUNING_HALVING" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/tuning-halving/knative_yamls/s3/service-driver.yaml
        kubectl apply -f $BENCHMARKS/tuning-halving/knative_yamls/s3/service-trainer.yaml
	benchmarks_deployed+=("TUNING HALVING")
fi
	
if [ "$DEPLOY_VIDEO_ANALYTICS" -eq 1 ]; then
        kubectl apply -f $BENCHMARKS/video-analytics/yamls/knative/inline/service-decoder.yaml
        kubectl apply -f $BENCHMARKS/video-analytics/yamls/knative/inline/service-recog.yaml
        kubectl apply -f $BENCHMARKS/video-analytics/yamls/knative/inline/service-streaming.yaml
        benchmarks_deployed+=("VIDEO ANALYTICS")
fi


echo "Following Benchmarks are deployed:"
for index in "${!benchmarks_deployed[@]}"; do
	echo "$((index+1))    ${benchmarks_deployed[$index]}"
done
