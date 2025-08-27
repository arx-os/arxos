package query

// QueryEngine defines the interface for all query engines
type QueryEngine interface {
	ExecuteQuery(queryStr string) (*AQLResult, error)
	Cleanup()
}

// Ensure our engines implement the interface
var _ QueryEngine = (*ArxObjectQueryEngine)(nil)
var _ QueryEngine = (*FileBasedQueryEngine)(nil)