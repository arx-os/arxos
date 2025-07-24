package database

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	"go.uber.org/zap"
)

// TransactionStatus represents the status of a transaction
type TransactionStatus string

const (
	TxStatusPending    TransactionStatus = "pending"
	TxStatusActive     TransactionStatus = "active"
	TxStatusCommitted  TransactionStatus = "committed"
	TxStatusRolledBack TransactionStatus = "rolled_back"
	TxStatusError      TransactionStatus = "error"
)

// TransactionInfo represents information about a transaction
type TransactionInfo struct {
	ID           string             `json:"id"`
	Status       TransactionStatus  `json:"status"`
	CreatedAt    time.Time          `json:"created_at"`
	StartedAt    time.Time          `json:"started_at"`
	CommittedAt  *time.Time         `json:"committed_at"`
	RolledBackAt *time.Time         `json:"rolled_back_at"`
	Duration     time.Duration      `json:"duration"`
	Error        string             `json:"error"`
	Queries      []string           `json:"queries"`
	Isolation    sql.IsolationLevel `json:"isolation"`
}

// TransactionManager provides transaction management functionality
type TransactionManager struct {
	dbService *DatabaseService
	logger    *zap.Logger
	mu        sync.RWMutex
	active    map[string]*TransactionInfo
}

// NewTransactionManager creates a new transaction manager
func NewTransactionManager(logger *zap.Logger) *TransactionManager {
	return &TransactionManager{
		logger: logger,
		active: make(map[string]*TransactionInfo),
	}
}

// BeginTransaction begins a new transaction
func (tm *TransactionManager) BeginTransaction(ctx context.Context, isolation sql.IsolationLevel) (*sql.Tx, *TransactionInfo, error) {
	tx, err := tm.dbService.db.BeginTx(ctx, &sql.TxOptions{
		Isolation: isolation,
		ReadOnly:  false,
	})
	if err != nil {
		return nil, nil, fmt.Errorf("failed to begin transaction: %w", err)
	}

	txInfo := &TransactionInfo{
		ID:        generateTransactionID(),
		Status:    TxStatusActive,
		CreatedAt: time.Now(),
		StartedAt: time.Now(),
		Isolation: isolation,
		Queries:   []string{},
	}

	tm.mu.Lock()
	tm.active[txInfo.ID] = txInfo
	tm.mu.Unlock()

	tm.logger.Info("Transaction begun",
		zap.String("tx_id", txInfo.ID),
		zap.String("isolation", isolation.String()))

	return tx, txInfo, nil
}

// BeginReadOnlyTransaction begins a read-only transaction
func (tm *TransactionManager) BeginReadOnlyTransaction(ctx context.Context, isolation sql.IsolationLevel) (*sql.Tx, *TransactionInfo, error) {
	tx, err := tm.dbService.db.BeginTx(ctx, &sql.TxOptions{
		Isolation: isolation,
		ReadOnly:  true,
	})
	if err != nil {
		return nil, nil, fmt.Errorf("failed to begin read-only transaction: %w", err)
	}

	txInfo := &TransactionInfo{
		ID:        generateTransactionID(),
		Status:    TxStatusActive,
		CreatedAt: time.Now(),
		StartedAt: time.Now(),
		Isolation: isolation,
		Queries:   []string{},
	}

	tm.mu.Lock()
	tm.active[txInfo.ID] = txInfo
	tm.mu.Unlock()

	tm.logger.Info("Read-only transaction begun",
		zap.String("tx_id", txInfo.ID),
		zap.String("isolation", isolation.String()))

	return tx, txInfo, nil
}

// CommitTransaction commits a transaction
func (tm *TransactionManager) CommitTransaction(tx *sql.Tx, txInfo *TransactionInfo) error {
	if txInfo == nil {
		return fmt.Errorf("transaction info is required")
	}

	start := time.Now()
	err := tx.Commit()
	duration := time.Since(start)

	tm.mu.Lock()
	defer tm.mu.Unlock()

	if err != nil {
		txInfo.Status = TxStatusError
		txInfo.Error = err.Error()
		txInfo.Duration = duration

		tm.logger.Error("Transaction commit failed",
			zap.String("tx_id", txInfo.ID),
			zap.Error(err),
			zap.Duration("duration", duration))

		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	now := time.Now()
	txInfo.Status = TxStatusCommitted
	txInfo.CommittedAt = &now
	txInfo.Duration = duration

	delete(tm.active, txInfo.ID)

	tm.logger.Info("Transaction committed",
		zap.String("tx_id", txInfo.ID),
		zap.Duration("duration", duration),
		zap.Int("query_count", len(txInfo.Queries)))

	return nil
}

// RollbackTransaction rolls back a transaction
func (tm *TransactionManager) RollbackTransaction(tx *sql.Tx, txInfo *TransactionInfo) error {
	if txInfo == nil {
		return fmt.Errorf("transaction info is required")
	}

	start := time.Now()
	err := tx.Rollback()
	duration := time.Since(start)

	tm.mu.Lock()
	defer tm.mu.Unlock()

	if err != nil {
		txInfo.Status = TxStatusError
		txInfo.Error = err.Error()
		txInfo.Duration = duration

		tm.logger.Error("Transaction rollback failed",
			zap.String("tx_id", txInfo.ID),
			zap.Error(err),
			zap.Duration("duration", duration))

		return fmt.Errorf("failed to rollback transaction: %w", err)
	}

	now := time.Now()
	txInfo.Status = TxStatusRolledBack
	txInfo.RolledBackAt = &now
	txInfo.Duration = duration

	delete(tm.active, txInfo.ID)

	tm.logger.Info("Transaction rolled back",
		zap.String("tx_id", txInfo.ID),
		zap.Duration("duration", duration),
		zap.Int("query_count", len(txInfo.Queries)))

	return nil
}

// ExecuteInTransaction executes a function within a transaction
func (tm *TransactionManager) ExecuteInTransaction(ctx context.Context, fn func(*sql.Tx) error, isolation sql.IsolationLevel) error {
	tx, txInfo, err := tm.BeginTransaction(ctx, isolation)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}

	defer func() {
		if r := recover(); r != nil {
			tm.logger.Error("Transaction panic",
				zap.String("tx_id", txInfo.ID),
				zap.Any("panic", r))

			if err := tx.Rollback(); err != nil {
				tm.logger.Error("Failed to rollback transaction after panic",
					zap.String("tx_id", txInfo.ID),
					zap.Error(err))
			}
			panic(r)
		}
	}()

	if err := fn(tx); err != nil {
		if rollbackErr := tm.RollbackTransaction(tx, txInfo); rollbackErr != nil {
			tm.logger.Error("Failed to rollback transaction",
				zap.String("tx_id", txInfo.ID),
				zap.Error(rollbackErr))
		}
		return fmt.Errorf("transaction execution failed: %w", err)
	}

	if err := tm.CommitTransaction(tx, txInfo); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// ExecuteReadOnlyInTransaction executes a read-only function within a transaction
func (tm *TransactionManager) ExecuteReadOnlyInTransaction(ctx context.Context, fn func(*sql.Tx) error, isolation sql.IsolationLevel) error {
	tx, txInfo, err := tm.BeginReadOnlyTransaction(ctx, isolation)
	if err != nil {
		return fmt.Errorf("failed to begin read-only transaction: %w", err)
	}

	defer func() {
		if r := recover(); r != nil {
			tm.logger.Error("Read-only transaction panic",
				zap.String("tx_id", txInfo.ID),
				zap.Any("panic", r))

			if err := tx.Rollback(); err != nil {
				tm.logger.Error("Failed to rollback read-only transaction after panic",
					zap.String("tx_id", txInfo.ID),
					zap.Error(err))
			}
			panic(r)
		}
	}()

	if err := fn(tx); err != nil {
		if rollbackErr := tm.RollbackTransaction(tx, txInfo); rollbackErr != nil {
			tm.logger.Error("Failed to rollback read-only transaction",
				zap.String("tx_id", txInfo.ID),
				zap.Error(rollbackErr))
		}
		return fmt.Errorf("read-only transaction execution failed: %w", err)
	}

	if err := tm.CommitTransaction(tx, txInfo); err != nil {
		return fmt.Errorf("failed to commit read-only transaction: %w", err)
	}

	return nil
}

// GetActiveTransactions returns all active transactions
func (tm *TransactionManager) GetActiveTransactions() []*TransactionInfo {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	var active []*TransactionInfo
	for _, txInfo := range tm.active {
		active = append(active, txInfo)
	}

	return active
}

// GetTransactionInfo returns information about a specific transaction
func (tm *TransactionManager) GetTransactionInfo(txID string) (*TransactionInfo, bool) {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	txInfo, exists := tm.active[txID]
	return txInfo, exists
}

// AddQueryToTransaction adds a query to the transaction's query log
func (tm *TransactionManager) AddQueryToTransaction(txInfo *TransactionInfo, query string) {
	if txInfo == nil {
		return
	}

	tm.mu.Lock()
	defer tm.mu.Unlock()

	txInfo.Queries = append(txInfo.Queries, query)
}

// GetTransactionStats returns transaction statistics
func (tm *TransactionManager) GetTransactionStats() map[string]interface{} {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	stats := map[string]interface{}{
		"active_transactions": len(tm.active),
		"total_queries":       0,
		"average_duration":    time.Duration(0),
	}

	var totalQueries int
	var totalDuration time.Duration
	var count int

	for _, txInfo := range tm.active {
		totalQueries += len(txInfo.Queries)
		if txInfo.Duration > 0 {
			totalDuration += txInfo.Duration
			count++
		}
	}

	stats["total_queries"] = totalQueries
	if count > 0 {
		stats["average_duration"] = totalDuration / time.Duration(count)
	}

	return stats
}

// CleanupStaleTransactions cleans up stale transactions
func (tm *TransactionManager) CleanupStaleTransactions(maxAge time.Duration) {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	now := time.Now()
	staleCount := 0

	for txID, txInfo := range tm.active {
		if now.Sub(txInfo.StartedAt) > maxAge {
			txInfo.Status = TxStatusError
			txInfo.Error = "Transaction timed out"
			delete(tm.active, txID)
			staleCount++
		}
	}

	if staleCount > 0 {
		tm.logger.Warn("Cleaned up stale transactions",
			zap.Int("count", staleCount),
			zap.Duration("max_age", maxAge))
	}
}

// generateTransactionID generates a unique transaction ID
func generateTransactionID() string {
	return fmt.Sprintf("tx_%d", time.Now().UnixNano())
}

// TransactionScope provides a scoped transaction with automatic cleanup
type TransactionScope struct {
	tx     *sql.Tx
	txInfo *TransactionInfo
	tm     *TransactionManager
	ctx    context.Context
}

// NewTransactionScope creates a new transaction scope
func (tm *TransactionManager) NewTransactionScope(ctx context.Context, isolation sql.IsolationLevel) (*TransactionScope, error) {
	tx, txInfo, err := tm.BeginTransaction(ctx, isolation)
	if err != nil {
		return nil, err
	}

	return &TransactionScope{
		tx:     tx,
		txInfo: txInfo,
		tm:     tm,
		ctx:    ctx,
	}, nil
}

// NewReadOnlyTransactionScope creates a new read-only transaction scope
func (tm *TransactionManager) NewReadOnlyTransactionScope(ctx context.Context, isolation sql.IsolationLevel) (*TransactionScope, error) {
	tx, txInfo, err := tm.BeginReadOnlyTransaction(ctx, isolation)
	if err != nil {
		return nil, err
	}

	return &TransactionScope{
		tx:     tx,
		txInfo: txInfo,
		tm:     tm,
		ctx:    ctx,
	}, nil
}

// GetTx returns the underlying transaction
func (ts *TransactionScope) GetTx() *sql.Tx {
	return ts.tx
}

// GetTxInfo returns the transaction info
func (ts *TransactionScope) GetTxInfo() *TransactionInfo {
	return ts.txInfo
}

// Commit commits the transaction
func (ts *TransactionScope) Commit() error {
	return ts.tm.CommitTransaction(ts.tx, ts.txInfo)
}

// Rollback rolls back the transaction
func (ts *TransactionScope) Rollback() error {
	return ts.tm.RollbackTransaction(ts.tx, ts.txInfo)
}

// AddQuery adds a query to the transaction log
func (ts *TransactionScope) AddQuery(query string) {
	ts.tm.AddQueryToTransaction(ts.txInfo, query)
}

// Close closes the transaction scope (rolls back if not committed)
func (ts *TransactionScope) Close() error {
	if ts.txInfo.Status == TxStatusActive {
		return ts.Rollback()
	}
	return nil
}
