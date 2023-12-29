// MIT License
//
// Copyright (c) 2020 Dmitrii Ustiugov and EASE lab
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"

	"github.com/vhive-serverless/vSwarm/tools/benchmarking_eventing/vhivemetadata"
	// "github.com/vhive-serverless/vSwarm/tools/endpoint"
	tracing "github.com/vhive-serverless/vSwarm/utils/tracing/go"

	pb "github.com/vhive-serverless/vSwarm/tools/invoker/proto"
)

const TimeseriesDBAddr = "10.96.0.84:90"

var (
	completed   int64
	completed_in_interval int64
	latSlice    LatencySlice
	portFlag    *int
	grpcTimeout time.Duration
	withTracing *bool
	workflowIDs map[string]string
)

type InvocationTimestamp struct {
	Timestamp []int64	`json:"timestamp"`
	Endpoints []string	`json:"endpoint"`
}

func main() {
	traceEndpointsFile := flag.String("traceFile", "load.json", "File with trace endpoints' metadata")
	latencyOutputFile := flag.String("latf", "lat.csv", "CSV file for the latency measurements in microseconds")
	portFlag = flag.Int("port", 80, "The port that functions listen to")
	withTracing = flag.Bool("trace", false, "Enable tracing in the client")
	zipkin := flag.String("zipkin", "http://localhost:9411/api/v2/spans", "zipkin url")
	debug := flag.Bool("dbg", false, "Enable debug logging")
	grpcTimeout = time.Duration(*flag.Int("grpcTimeout", 30, "Timeout in seconds for gRPC requests")) * time.Second

	flag.Parse()

	log.SetFormatter(&log.TextFormatter{
		TimestampFormat: time.RFC3339Nano,
		FullTimestamp:   true,
	})
	log.SetOutput(os.Stdout)
	if *debug {
		log.SetLevel(log.DebugLevel)
		log.Debug("Debug logging is enabled")
	} else {
		log.SetLevel(log.InfoLevel)
	}
	
	// TODO: This needs to be done by passing the filename as parameter
	log.Info("Reading the endpoints from the file: ", *traceEndpointsFile)

	invocations, err := readTraceEndpoints(*traceEndpointsFile)
	if err != nil {
		log.Fatal("Failed to read the trace endpoints file: ", err)
	}

	workflowIDs = make(map[string]string)
	for _, iv := range invocations {
		for _, ep := range iv.Endpoints {
			if _, exists := workflowIDs[ep]; !exists {
				workflowIDs[ep] = uuid.New().String()
			}
		}
	}

	if *withTracing {
		shutdown, err := tracing.InitBasicTracer(*zipkin, "invoker")
		if err != nil {
			log.Print(err)
		}
		defer shutdown()
	}

	// TODO: Warmup time, Granularity must be read from the configuration file and appropriately passed
	err = runExperiment(invocations, 2, "minute")

	writeLatencies(*latencyOutputFile)
}

func readTraceEndpoints(path string) (invocations []*InvocationTimestamp, _ error){
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal(data, &invocations); err != nil {
		return nil, err
	}
	return 
}


func runMinuteTrace(invocation InvocationTimestamp, granularity string) {
	log.Info("Timestamp: ", invocation.Timestamp)
	log.Info("Endpoints: ", invocation.Endpoints)

	numberOfInvocations := len(invocation.Timestamp)		

	invocationNo := 0
	var previousIAT int64

loop:
	for {
		iat := time.Duration(invocation.Timestamp[invocationNo]) * time.Microsecond  
		sleepFor := iat.Microseconds() - previousIAT
		time.Sleep(time.Duration(sleepFor) * time.Microsecond)
		// go invokeFunction(invocation.Endpoints[invocationNo])
		go invokeServingFunction(invocation.Endpoints[invocationNo])

		invocationNo += 1
		previousIAT = iat.Microseconds()
		if (invocationNo >= numberOfInvocations) {
			break loop
		}
	}
}

// func invokeFunction(endpoint string) {
// 	log.Info("Endpoint: ", endpoint)
// }


// TODO: add all debug statements. Log statements.
func runExperiment(invocations []*InvocationTimestamp, warmupTime int, granularity string) (_ error) {

	numberOfMinutes := len(invocations)
	if (warmupTime > numberOfMinutes) {
		log.Warnf("Warm up time larger than total experiment time. Setting warm up time to 1")
		warmupTime = 1
	}

	var waitDuration time.Duration
	switch granularity {
	case "second":
		waitDuration = 1 * time.Second
	case "minute":
		waitDuration = 1 * time.Minute
	default:
		log.Warnf("Invalid Granularity. Granularity set to a second.")
		waitDuration = 1 * time.Second
	}
	tick := time.Tick (waitDuration)

	var minute int
	minute = 0	

loop:
	for {
		select {
		case <- tick:
			if (minute == 0) { 
				log.Info("Running Warmup Phase") 
			}
			if (minute == warmupTime) { 
				log.Info("Warmup Phase Completed")
				log.Info("Running Experiment Phase")
			}
			if (minute >= numberOfMinutes) { 
				log.Info("Experiment Phase Completed")
				break loop
			}
			go runMinuteTrace(*invocations[minute], granularity)
			minute += 1
		}
	}
		
	return nil
}




// func runExperimentTemp(endpoints []*endpoint.Endpoint, runDuration int, targetRPS float64) (realRPS float64) {
// 	var issued int

// 	Start(TimeseriesDBAddr, endpoints, workflowIDs)
// 	timeout := time.After(time.Duration(runDuration) * time.Second)
// 	tick := time.Tick(time.Duration(1000000/targetRPS) * time.Microsecond)
// 	start := time.Now()

// 	completed = 0

// loop:
// 	for {
// 		ep := endpoints[issued%len(endpoints)]
// 		go invokeServingFunction(ep)
// 		issued++

// 		select {

// 		case <-timeout:
// 			break loop

// 		case <-tick:
// 			continue

// 		}
// 	}

// 	duration := time.Since(start).Seconds()
// 	realRPS = float64(completed) / duration
// 	addDurations(End())
// 	log.Infof("Issued / completed requests: %d, %d", issued, completed)
// 	log.Infof("Real / target RPS: %.2f / %v", realRPS, targetRPS)
// 	log.Println("Experiment finished!")
// 	return
// }

func SayHello(address, workflowID string) {
	dialOptions := make([]grpc.DialOption, 0)
	dialOptions = append(dialOptions, grpc.WithTransportCredentials(insecure.NewCredentials()), grpc.WithBlock())
	if *withTracing {
		dialOptions = append(dialOptions, grpc.WithUnaryInterceptor(otelgrpc.UnaryClientInterceptor()))
	}
	conn, err := grpc.Dial(address, dialOptions...)
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close()

	c := pb.NewGreeterClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), grpcTimeout)
	defer cancel()

	_, err = c.SayHello(ctx, &pb.HelloRequest{
		Name: "Invoke relay",
		VHiveMetadata: vhivemetadata.MakeVHiveMetadata(
			workflowID,
			uuid.New().String(),
			time.Now().UTC(),
		),
	})
	if err != nil {
		log.Warnf("Failed to invoke %v, err=%v", address, err)
	} else {
		atomic.AddInt64(&completed, 1)
	}
}

func invokeServingFunction(endpointHostname string) {
	defer getDuration(startMeasurement(endpointHostname)) // measure entire invocation time

	address := fmt.Sprintf("%s:%d", endpointHostname, *portFlag)
	log.Debug("Invoking: ", address)

	SayHello(address, workflowIDs[endpointHostname])
}

// LatencySlice is a thread-safe slice to hold a slice of latency measurements.
type LatencySlice struct {
	sync.Mutex
	slice []int64
}

func startMeasurement(msg string) (string, time.Time) {
	return msg, time.Now()
}

func getDuration(msg string, start time.Time) {
	latency := time.Since(start)
	log.Debugf("Invoked %v in %v usec\n", msg, latency.Microseconds())
	addDurations([]time.Duration{latency})
}

func addDurations(ds []time.Duration) {
	latSlice.Lock()
	for _, d := range ds {
		latSlice.slice = append(latSlice.slice, d.Microseconds())
	}
	latSlice.Unlock()
}

func writeLatencies(latencyOutputFile string) {
	latSlice.Lock()
	defer latSlice.Unlock()

	fileName := fmt.Sprintf("rps_%s", latencyOutputFile)
	log.Info("The measured latencies are saved in ", fileName)

	file, err := os.OpenFile(fileName, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)

	if err != nil {
		log.Fatal("Failed creating file: ", err)
	}

	datawriter := bufio.NewWriter(file)

	for _, lat := range latSlice.slice {
		_, err := datawriter.WriteString(strconv.FormatInt(lat, 10) + "\n")
		if err != nil {
			log.Fatal("Failed to write the URLs to a file ", err)
		}
	}

	datawriter.Flush()
	file.Close()
}
