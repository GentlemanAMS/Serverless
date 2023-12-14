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
	"os/exec"

	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"

	"github.com/vhive-serverless/vSwarm/tools/benchmarking_eventing/vhivemetadata"
	"github.com/vhive-serverless/vSwarm/tools/endpoint"
	tracing "github.com/vhive-serverless/vSwarm/utils/tracing/go"

	pb "github.com/vhive-serverless/vSwarm/tools/invoker/proto"
)

const TimeseriesDBAddr = "10.96.0.84:90"

var (
	completed   int64
	latSlice    LatencySlice
	portFlag    *int
	grpcTimeout time.Duration
	withTracing *bool
	workflowIDs map[*endpoint.Endpoint]string
)

func main() {
	endpointsFile := flag.String("endpointsFile", "endpoints.json", "File with endpoints' metadata")
	rps := flag.Float64("rps", 1.0, "Target requests per second")
	runDuration := flag.Int("time", 5, "Run the experiment for X seconds")
	latencyOutputFile := flag.String("latf", "lat.csv", "CSV file for the latency measurements in microseconds")
	portFlag = flag.Int("port", 80, "The port that functions listen to")
	withTracing = flag.Bool("trace", false, "Enable tracing in the client")
	zipkin := flag.String("zipkin", "http://localhost:9411/api/v2/spans", "zipkin url")
	debug := flag.Bool("dbg", false, "Enable debug logging")
	grpcTimeout = time.Duration(*flag.Int("grpcTimeout", 30, "Timeout in seconds for gRPC requests")) * time.Second
	perfFile := flag.String("perf", "perf.dat", "Path to the perf data file")
	mpstatFile := flag.String("mpstat", "mpstat.dat", "Path to the mpstat data file")
	podanalysisPythonFile := flag.String("podanalpy", "podanalysis.py", "Path to the pod analysis python file")
	podanalysisOutputFile := flag.String("podanaloutput", "podanalysis.json", "Path to the pod analysis output json file")
	statInterval := flag.Int("statinterval", 30000, "Interval at which stats are collected in milliseconds")

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

	log.Info("Reading the endpoints from the file: ", *endpointsFile)

	endpoints, err := readEndpoints(*endpointsFile)
	if err != nil {
		log.Fatal("Failed to read the endpoints file: ", err)
	}

	workflowIDs = make(map[*endpoint.Endpoint]string)
	for _, ep := range endpoints {
		workflowIDs[ep] = uuid.New().String()
	}

	if *withTracing {
		shutdown, err := tracing.InitBasicTracer(*zipkin, "invoker")
		if err != nil {
			log.Print(err)
		}
		defer shutdown()
	}

	realRPS := runExperiment(endpoints, *runDuration, *rps, *perfFile, *mpstatFile, *podanalysisPythonFile, *podanalysisOutputFile, *statInterval)

	writeLatencies(realRPS, *latencyOutputFile)
}

func readEndpoints(path string) (endpoints []*endpoint.Endpoint, _ error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal(data, &endpoints); err != nil {
		return nil, err
	}
	return
}

func warmupExpt(endpoints []*endpoint.Endpoint, runDuration int, targetRPS float64) {
	var issued int

	Start(TimeseriesDBAddr, endpoints, workflowIDs)

	timeout := time.After(time.Duration(runDuration) * time.Second)
	tick := time.Tick(time.Duration(1000/targetRPS) * time.Millisecond)
	start := time.Now()
loop:
	for {
		ep := endpoints[issued%len(endpoints)]
		if ep.Eventing {
			go invokeEventingFunction(ep)
		} else {
			go invokeServingFunction(ep)
		}
		issued++

		select {
		case <-timeout:
			break loop
		case <-tick:
			continue
		}
	}

	duration := time.Since(start).Seconds()
	realRPS := float64(completed) / duration
	// addDurations(End())
	log.Infof("WarmUp: Issued / completed requests: %d, %d", issued, completed)
	log.Infof("WarmUp: Real / target RPS: %.2f / %v", realRPS, targetRPS)
	completed = 0
	return
}

func runExperiment(endpoints []*endpoint.Endpoint, runDuration int, targetRPS float64, perfoutputFilename string, mpstatoutputFilename string, podanalysisPythonFilename string, podanalysisOutputFilename string, timeinterval_ms int) (realRPS float64) {
	var issued int

	// Warmup Process
	var warmupRPS float64
	var warmpupRunDuration int
	for i := 0.1; i <= 1; i += 0.1 {
		warmupRPS = targetRPS * i
		warmpupRunDuration = int(float64(runDuration) * 0.04)
		warmupExpt(endpoints, warmpupRunDuration, warmupRPS)
	}

	// Actual process 
	statstart_ms := runDuration * 100 // Start after 10% of runDuration in milliseconds: 0.1 * 1000 = 100
	intervalcount := (runDuration * 800) / (timeinterval_ms)

	perfstartString := strconv.Itoa(statstart_ms)
	intervalcountString := strconv.Itoa(intervalcount)
	timeintervalinmsString := strconv.Itoa(timeinterval_ms)
	perfcmd := exec.Command("sudo", "perf", "stat", "-e", "instructions,LLC-loads,LLC-load-misses,LLC-stores,LLC-store-misses,LLC-prefetch-misses", "--delay", perfstartString, "-I", timeintervalinmsString, "--interval-count", intervalcountString, "-o", perfoutputFilename)

	timeinterval := timeinterval_ms / 1000
	timeintervalString := strconv.Itoa(timeinterval)

	mpstatoutputFile, err := os.Create(mpstatoutputFilename)
	if err != nil {
		log.Fatalf("Error creating output file: %v", err)
	}
	mpstatcmd := exec.Command("mpstat", timeintervalString, intervalcountString)
	mpstatcmd.Stdout = mpstatoutputFile


	Start(TimeseriesDBAddr, endpoints, workflowIDs)

	perfcmd.Start()

	stat := time.After(time.Duration(statstart_ms / 1000) * time.Second)
	timeout := time.After(time.Duration(runDuration) * time.Second)
	tick := time.Tick(time.Duration(1000/targetRPS) * time.Millisecond)
	start := time.Now()

loop:
	for {
		ep := endpoints[issued%len(endpoints)]
		if ep.Eventing {
			go invokeEventingFunction(ep)
		} else {
			go invokeServingFunction(ep)
		}
		issued++

		select {
		case <- stat:
			mpstatcmd.Start()
			time_elapsed := time.Since(start)
			podanalysiscmd := exec.Command("python3", podanalysisPythonFilename, podanalysisOutputFilename, time_elapsed.String())
			podanalysiscmd.Start()
		case <-timeout:
			break loop
		case <-tick:
			continue
		}
	}

	perferr := perfcmd.Wait()
    if perferr != nil {
        log.Warnf("Perf failure: %v", perferr)
    }
	mpstaterr := mpstatcmd.Wait()
    if mpstaterr != nil {
        log.Warnf("MPStat failure: %v", mpstaterr)
    }
	mpstatoutputFile.Close()

	duration := time.Since(start).Seconds()
	realRPS = float64(completed) / duration
	addDurations(End())
	log.Infof("Issued / completed requests: %d, %d", issued, completed)
	log.Infof("Real / target RPS: %.2f / %v", realRPS, targetRPS)
	log.Println("Experiment finished!")
	return
}

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

func invokeEventingFunction(endpoint *endpoint.Endpoint) {
	address := fmt.Sprintf("%s:%d", endpoint.Hostname, *portFlag)
	log.Debug("Invoking asynchronously: ", address)

	SayHello(address, workflowIDs[endpoint])
}

func invokeServingFunction(endpoint *endpoint.Endpoint) {
	defer getDuration(startMeasurement(endpoint.Hostname)) // measure entire invocation time

	address := fmt.Sprintf("%s:%d", endpoint.Hostname, *portFlag)
	log.Debug("Invoking: ", address)

	SayHello(address, workflowIDs[endpoint])
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

func writeLatencies(rps float64, latencyOutputFile string) {
	latSlice.Lock()
	defer latSlice.Unlock()

	fileName := fmt.Sprintf("rps%.2f_%s", rps, latencyOutputFile)
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
