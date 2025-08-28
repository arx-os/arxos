package bilt

import (
	"fmt"
	"sync"
	"time"
)

// Ledger manages BILT token transactions and balances
type Ledger struct {
	mu           sync.RWMutex
	balances     map[string]float64
	transactions []Transaction
	userHistory  map[string][]Transaction
}

// Transaction represents a BILT token transaction
type Transaction struct {
	ID          string
	UserID      string
	Amount      float64
	Type        string    // earning, spending, transfer, bonus
	Reason      string
	Timestamp   time.Time
	Status      string    // pending, completed, failed
	Reference   string    // Reference to contribution or purchase
	Metadata    map[string]interface{}
}

// ContributionResult represents the result of processing a contribution
type ContributionResult struct {
	ContributionID string
	UserID         string
	Timestamp      time.Time
	ObjectPath     string
	DataType       string
	TokensEarned   float64
	QualityScore   QualityScore
	Status         string
	Message        string
}

// NewLedger creates a new BILT token ledger
func NewLedger() *Ledger {
	return &Ledger{
		balances:     make(map[string]float64),
		transactions: []Transaction{},
		userHistory:  make(map[string][]Transaction),
	}
}

// RecordTransaction records a new BILT token transaction
func (l *Ledger) RecordTransaction(tx Transaction) error {
	l.mu.Lock()
	defer l.mu.Unlock()
	
	// Validate transaction
	if tx.UserID == "" {
		return fmt.Errorf("transaction must have a user ID")
	}
	
	if tx.Amount == 0 {
		return fmt.Errorf("transaction amount cannot be zero")
	}
	
	// Update balance based on transaction type
	switch tx.Type {
	case "earning", "bonus":
		l.balances[tx.UserID] += tx.Amount
	case "spending", "transfer_out":
		if l.balances[tx.UserID] < tx.Amount {
			return fmt.Errorf("insufficient balance: have %.4f, need %.4f", 
				l.balances[tx.UserID], tx.Amount)
		}
		l.balances[tx.UserID] -= tx.Amount
	case "transfer_in":
		l.balances[tx.UserID] += tx.Amount
	default:
		return fmt.Errorf("unknown transaction type: %s", tx.Type)
	}
	
	// Record transaction
	l.transactions = append(l.transactions, tx)
	
	// Add to user history
	if _, exists := l.userHistory[tx.UserID]; !exists {
		l.userHistory[tx.UserID] = []Transaction{}
	}
	l.userHistory[tx.UserID] = append(l.userHistory[tx.UserID], tx)
	
	return nil
}

// GetBalance returns the current BILT token balance for a user
func (l *Ledger) GetBalance(userID string) (float64, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	if userID == "" {
		return 0, fmt.Errorf("user ID cannot be empty")
	}
	
	balance, exists := l.balances[userID]
	if !exists {
		return 0, nil // New user starts with 0 balance
	}
	
	return balance, nil
}

// GetUserHistory returns transaction history for a user
func (l *Ledger) GetUserHistory(userID string, limit int) ([]Transaction, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	if userID == "" {
		return nil, fmt.Errorf("user ID cannot be empty")
	}
	
	history, exists := l.userHistory[userID]
	if !exists {
		return []Transaction{}, nil
	}
	
	// Return most recent transactions first
	result := make([]Transaction, 0, limit)
	start := len(history) - limit
	if start < 0 {
		start = 0
	}
	
	for i := len(history) - 1; i >= start; i-- {
		result = append(result, history[i])
	}
	
	return result, nil
}

// GetTotalSupply returns the total BILT tokens in circulation
func (l *Ledger) GetTotalSupply() float64 {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	total := 0.0
	for _, balance := range l.balances {
		total += balance
	}
	
	return total
}

// GetTopEarners returns the users with the highest BILT token balances
func (l *Ledger) GetTopEarners(limit int) []UserBalance {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	// Create slice of user balances
	userBalances := make([]UserBalance, 0, len(l.balances))
	for userID, balance := range l.balances {
		userBalances = append(userBalances, UserBalance{
			UserID:  userID,
			Balance: balance,
		})
	}
	
	// Sort by balance (descending)
	// In production, use sort.Slice
	for i := 0; i < len(userBalances); i++ {
		for j := i + 1; j < len(userBalances); j++ {
			if userBalances[j].Balance > userBalances[i].Balance {
				userBalances[i], userBalances[j] = userBalances[j], userBalances[i]
			}
		}
	}
	
	// Return top N
	if limit > len(userBalances) {
		limit = len(userBalances)
	}
	
	return userBalances[:limit]
}

// TransferTokens transfers BILT tokens between users
func (l *Ledger) TransferTokens(fromUserID, toUserID string, amount float64, reason string) error {
	l.mu.Lock()
	defer l.mu.Unlock()
	
	// Validate
	if fromUserID == toUserID {
		return fmt.Errorf("cannot transfer to same user")
	}
	
	if amount <= 0 {
		return fmt.Errorf("transfer amount must be positive")
	}
	
	// Check balance
	if l.balances[fromUserID] < amount {
		return fmt.Errorf("insufficient balance for transfer")
	}
	
	// Create transactions
	txID := generateTransactionID()
	timestamp := time.Now()
	
	// Debit transaction
	debitTx := Transaction{
		ID:        txID + "_debit",
		UserID:    fromUserID,
		Amount:    amount,
		Type:      "transfer_out",
		Reason:    reason,
		Timestamp: timestamp,
		Status:    "completed",
		Reference: toUserID,
	}
	
	// Credit transaction
	creditTx := Transaction{
		ID:        txID + "_credit",
		UserID:    toUserID,
		Amount:    amount,
		Type:      "transfer_in",
		Reason:    reason,
		Timestamp: timestamp,
		Status:    "completed",
		Reference: fromUserID,
	}
	
	// Update balances
	l.balances[fromUserID] -= amount
	l.balances[toUserID] += amount
	
	// Record transactions
	l.transactions = append(l.transactions, debitTx, creditTx)
	
	// Update user histories
	if _, exists := l.userHistory[fromUserID]; !exists {
		l.userHistory[fromUserID] = []Transaction{}
	}
	l.userHistory[fromUserID] = append(l.userHistory[fromUserID], debitTx)
	
	if _, exists := l.userHistory[toUserID]; !exists {
		l.userHistory[toUserID] = []Transaction{}
	}
	l.userHistory[toUserID] = append(l.userHistory[toUserID], creditTx)
	
	return nil
}

// GetRecentTransactions returns the most recent transactions system-wide
func (l *Ledger) GetRecentTransactions(limit int) []Transaction {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	start := len(l.transactions) - limit
	if start < 0 {
		start = 0
	}
	
	result := make([]Transaction, 0, limit)
	for i := len(l.transactions) - 1; i >= start; i-- {
		result = append(result, l.transactions[i])
	}
	
	return result
}

// GetEarningsSummary returns earning statistics for a user
func (l *Ledger) GetEarningsSummary(userID string) (*EarningsSummary, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	history, exists := l.userHistory[userID]
	if !exists {
		return &EarningsSummary{
			UserID:        userID,
			TotalEarned:   0,
			TotalSpent:    0,
			CurrentBalance: 0,
		}, nil
	}
	
	summary := &EarningsSummary{
		UserID:         userID,
		CurrentBalance: l.balances[userID],
	}
	
	// Calculate totals
	for _, tx := range history {
		switch tx.Type {
		case "earning", "bonus", "transfer_in":
			summary.TotalEarned += tx.Amount
			summary.TransactionCount++
		case "spending", "transfer_out":
			summary.TotalSpent += tx.Amount
			summary.TransactionCount++
		}
		
		// Track first and last transaction
		if summary.FirstTransaction.IsZero() || tx.Timestamp.Before(summary.FirstTransaction) {
			summary.FirstTransaction = tx.Timestamp
		}
		if tx.Timestamp.After(summary.LastTransaction) {
			summary.LastTransaction = tx.Timestamp
		}
	}
	
	// Calculate average earning per transaction
	earningCount := 0
	for _, tx := range history {
		if tx.Type == "earning" {
			earningCount++
		}
	}
	
	if earningCount > 0 {
		summary.AverageEarning = summary.TotalEarned / float64(earningCount)
	}
	
	return summary, nil
}

// UserBalance represents a user's BILT token balance
type UserBalance struct {
	UserID  string
	Balance float64
}

// EarningsSummary represents a summary of user earnings
type EarningsSummary struct {
	UserID           string
	TotalEarned      float64
	TotalSpent       float64
	CurrentBalance   float64
	TransactionCount int
	AverageEarning   float64
	FirstTransaction time.Time
	LastTransaction  time.Time
}