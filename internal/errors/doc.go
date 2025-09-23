// Package errors is DEPRECATED.
//
// This package exists only for backward compatibility.
// All types and functions are now aliases/wrappers to pkg/errors.
//
// Please migrate your code to use:
//   github.com/arx-os/arxos/pkg/errors
//
// Migration is straightforward - simply update your import path:
//   // Old:
//   import "github.com/arx-os/arxos/internal/errors"
//
//   // New:
//   import "github.com/arx-os/arxos/pkg/errors"
//
// All APIs remain the same, so no code changes are required beyond
// updating the import path.
package errors