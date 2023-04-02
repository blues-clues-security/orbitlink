//@note: This is based on an outdated version of ol_control_receive.py

package main

import (
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"
)

const (
	address       = "0.0.0.0:12345"
	flushInterval = 1
)

func main() {
	addr, err := net.ResolveUDPAddr("udp", address)
	if err != nil {
		log.Fatalf("Failed to resolve address: %v", err)
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}
	defer conn.Close()

	file, err := os.OpenFile("ol_data_log.txt", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatalf("Failed to open file: %v", err)
	}
	defer file.Close()

	packetCounter := 0

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	for {
		select {
		case <-sigChan:
			fmt.Println("\n[!] Keyboard interrupt received\n[*] Closing the program...")
			os.Exit(0)

		default:
			err := conn.SetReadDeadline(time.Now().Add(1 * time.Second))
			if err != nil {
				log.Fatalf("Failed to set deadline: %v", err)
			}

			buf := make([]byte, 1024)
			n, srcAddr, err := conn.ReadFromUDP(buf)

			if err != nil {
				if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
					continue
				}
				log.Printf("Error reading from UDP: %v", err)
				continue
			}

			packetCounter++

			srcIP := buf[0:4]
			dstIP := buf[4:8]
			payloadLength := binary.BigEndian.Uint16(buf[8:10])
			sequenceNumber := binary.BigEndian.Uint16(buf[10:12])

			payload := buf[12:n]

			fmt.Printf("Received packet from %s\n", srcAddr)
			fmt.Printf("Source Address: %s\n", net.IP(srcIP))
			fmt.Printf("Destination Address: %s\n", net.IP(dstIP))
			fmt.Printf("Payload Length: %d\n", payloadLength)
			fmt.Printf("Sequence Number: %d\n", sequenceNumber)
			fmt.Printf("Payload Data: %x\n", payload)

			file.WriteString(fmt.Sprintf("Received packet from %s\n", srcAddr))
			file.WriteString(fmt.Sprintf("Source Address: %s\n", net.IP(srcIP)))
			file.WriteString(fmt.Sprintf("Destination Address: %s\n", net.IP(dstIP)))
			file.WriteString(fmt.Sprintf("Payload Length: %d\n", payloadLength))
			file.WriteString(fmt.Sprintf("Sequence Number: %d\n", sequenceNumber))
			file.WriteString(fmt.Sprintf("Payload Data: %x\n\n", payload))

			if packetCounter%flushInterval == 0 {
				file.Sync()
				fmt.Println("[*] Data written to file.")
			}
		}
	}
}