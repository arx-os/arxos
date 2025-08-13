module github.com/arxos/arxos-api

go 1.21

require (
	github.com/golang-jwt/jwt/v5 v5.2.0
	github.com/gorilla/mux v1.8.1
	github.com/gorilla/websocket v1.5.1
	github.com/arxos/arxos-core v0.0.0
	github.com/arxos/arxos-ingestion v0.0.0
	github.com/arxos/arxos-storage v0.0.0
)

replace github.com/arxos/arxos-core => ../arxos-core
replace github.com/arxos/arxos-ingestion => ../arxos-ingestion
replace github.com/arxos/arxos-storage => ../arxos-storage