# ARX Tokenomics Mathematical Model

## 🎯 **Overview**

This document defines the mathematical framework for ARX token economics, integrating with existing ArxLogic validation scores and platform revenue streams to create a sustainable and fair token ecosystem. ARX is structured as a revenue-sharing token, legally distinct from Arxos equity, providing holders with pro-rata shares of platform revenue from data sales and service transactions.

---

## 🧮 **Core Tokenomics Formulas**

### **1. ARX Minting Formula**

```python
def calculate_arx_mint(validation_score: float, complexity_multiplier: float, base_amount: float = 1.0) -> float:
    """
    Calculate ARX tokens to mint for a validated contribution.
    
    Args:
        validation_score: ArxLogic validation score (0.0 to 1.0)
        complexity_multiplier: System complexity multiplier
        base_amount: Base ARX amount for standard object (default: 1.0)
    
    Returns:
        float: ARX tokens to mint
    """
    return base_amount * validation_score * complexity_multiplier
```

### **2. Validation Score Components**

```python
def calculate_validation_score(
    simulation_pass_rate: float,
    ai_accuracy_rate: float,
    system_completion_score: float,
    error_propagation_score: float
) -> float:
    """
    Calculate comprehensive validation score from ArxLogic metrics.
    
    Args:
        simulation_pass_rate: % of objects passing behavioral simulation
        ai_accuracy_rate: Correct label validation rate
        system_completion_score: System completion percentage
        error_propagation_score: Error propagation impact (inverse)
    
    Returns:
        float: Weighted validation score (0.0 to 1.0)
    """
    weights = {
        'simulation': 0.35,
        'accuracy': 0.30,
        'completion': 0.20,
        'propagation': 0.15
    }
    
    # Convert error propagation to positive score (lower propagation = higher score)
    propagation_score = 1.0 - error_propagation_score
    
    validation_score = (
        simulation_pass_rate * weights['simulation'] +
        ai_accuracy_rate * weights['accuracy'] +
        system_completion_score * weights['completion'] +
        propagation_score * weights['propagation']
    )
    
    return min(max(validation_score, 0.0), 1.0)
```

### **3. Complexity Multipliers**

```python
COMPLEXITY_MULTIPLIERS = {
    'electrical': 1.0,      # Baseline
    'plumbing': 1.2,        # 20% more complex
    'hvac': 1.5,            # 50% more complex
    'fire_alarm': 1.7,      # 70% more complex
    'security': 2.0,        # 100% more complex
    'custom': 1.0           # Default for unknown systems
}

def get_complexity_multiplier(system_type: str) -> float:
    """Get complexity multiplier for system type."""
    return COMPLEXITY_MULTIPLIERS.get(system_type.lower(), COMPLEXITY_MULTIPLIERS['custom'])
```

---

## 💰 **Revenue Attribution & Dividend Distribution**

### **4. Revenue Pool Calculation (Legal Compliance)**

```python
def calculate_revenue_pool(
    api_usage_revenue: float,
    data_download_revenue: float,
    contractor_service_revenue: float,
    operational_costs: float = 0.0
) -> float:
    """
    Calculate total revenue pool for dividend distribution.
    
    IMPORTANT: Only platform revenue from data sales and service transactions
    is eligible for ARX dividends. Arxos equity profits, IP licensing,
    or VC funding are NOT included in the dividend pool.
    
    Args:
        api_usage_revenue: Revenue from API usage fees
        data_download_revenue: Revenue from data downloads
        contractor_service_revenue: Revenue from contractor services
        operational_costs: Operational costs to subtract
    
    Returns:
        float: Total dividend pool amount
    """
    total_revenue = api_usage_revenue + data_download_revenue + contractor_service_revenue
    dividend_pool = total_revenue - operational_costs
    
    return max(dividend_pool, 0.0)
```

### **5. Dividend Per Token Calculation**

```python
def calculate_dividend_per_token(total_revenue_pool: float, total_arx_supply: float) -> float:
    """
    Calculate dividend amount per ARX token.
    
    Args:
        total_revenue_pool: Total revenue available for dividends
        total_arx_supply: Total circulating ARX supply
    
    Returns:
        float: Dividend amount per token
    """
    if total_arx_supply <= 0:
        return 0.0
    
    return total_revenue_pool / total_arx_supply
```

### **6. Individual Dividend Calculation**

```python
def calculate_user_dividend(
    user_arx_balance: float,
    dividend_per_token: float,
    minimum_payout_threshold: float = 0.01
) -> float:
    """
    Calculate dividend payout for a specific user.
    
    Args:
        user_arx_balance: User's ARX token balance
        dividend_per_token: Dividend amount per token
        minimum_payout_threshold: Minimum payout amount (default: $0.01)
    
    Returns:
        float: Dividend payout amount
    """
    dividend_amount = user_arx_balance * dividend_per_token
    
    # Only pay out if above minimum threshold
    if dividend_amount < minimum_payout_threshold:
        return 0.0
    
    return dividend_amount
```

---

## 📊 **Economic Equilibrium Models**

### **7. Supply-Demand Equilibrium**

```python
def calculate_token_value_equilibrium(
    total_revenue: float,
    total_supply: float,
    market_demand_multiplier: float = 1.0,
    volatility_factor: float = 0.1
) -> dict:
    """
    Calculate theoretical token value based on revenue and supply.
    
    Args:
        total_revenue: Annual platform revenue
        total_supply: Total ARX supply
        market_demand_multiplier: Market demand factor
        volatility_factor: Price volatility factor
    
    Returns:
        dict: Equilibrium calculations
    """
    # Base value calculation
    base_value = total_revenue / total_supply if total_supply > 0 else 0.0
    
    # Apply market demand multiplier
    market_value = base_value * market_demand_multiplier
    
    # Calculate volatility range
    volatility_range = market_value * volatility_factor
    min_value = market_value - volatility_range
    max_value = market_value + volatility_range
    
    return {
        'base_value': base_value,
        'market_value': market_value,
        'min_value': max(min_value, 0.0),
        'max_value': max_value,
        'volatility_range': volatility_range
    }
```

### **8. Inflation/Deflation Mechanisms**

```python
def calculate_supply_adjustment(
    current_supply: float,
    target_inflation_rate: float = 0.05,  # 5% annual inflation
    revenue_growth_rate: float = 0.20,    # 20% revenue growth
    time_period_months: int = 12
) -> dict:
    """
    Calculate supply adjustment based on revenue growth and target inflation.
    
    Args:
        current_supply: Current total ARX supply
        target_inflation_rate: Target annual inflation rate
        revenue_growth_rate: Annual revenue growth rate
        time_period_months: Time period in months
    
    Returns:
        dict: Supply adjustment calculations
    """
    # Calculate target supply based on revenue growth
    revenue_multiplier = (1 + revenue_growth_rate) ** (time_period_months / 12)
    target_supply = current_supply * revenue_multiplier
    
    # Calculate inflation adjustment
    inflation_adjustment = current_supply * target_inflation_rate * (time_period_months / 12)
    
    # Final target supply
    final_target_supply = target_supply + inflation_adjustment
    
    # Supply change
    supply_change = final_target_supply - current_supply
    supply_change_rate = supply_change / current_supply if current_supply > 0 else 0.0
    
    return {
        'current_supply': current_supply,
        'target_supply': final_target_supply,
        'supply_change': supply_change,
        'supply_change_rate': supply_change_rate,
        'inflation_adjustment': inflation_adjustment,
        'revenue_multiplier': revenue_multiplier
    }
```

---

## 🔄 **Revenue Attribution Formulas**

### **9. Revenue Source Attribution**

```python
def calculate_revenue_attribution(
    api_usage_revenue: float,
    data_download_revenue: float,
    contractor_service_revenue: float
) -> dict:
    """
    Calculate revenue attribution percentages for transparency.
    
    Args:
        api_usage_revenue: Revenue from API usage
        data_download_revenue: Revenue from data downloads
        contractor_service_revenue: Revenue from contractor services
    
    Returns:
        dict: Revenue attribution breakdown
    """
    total_revenue = api_usage_revenue + data_download_revenue + contractor_service_revenue
    
    if total_revenue <= 0:
        return {
            'api_usage_percentage': 0.0,
            'data_download_percentage': 0.0,
            'contractor_service_percentage': 0.0,
            'total_revenue': 0.0
        }
    
    return {
        'api_usage_percentage': (api_usage_revenue / total_revenue) * 100,
        'data_download_percentage': (data_download_revenue / total_revenue) * 100,
        'contractor_service_percentage': (contractor_service_revenue / total_revenue) * 100,
        'total_revenue': total_revenue
    }
```

### **10. Dividend Distribution Efficiency**

```python
def calculate_distribution_efficiency(
    total_dividend_pool: float,
    distributed_amount: float,
    gas_costs: float = 0.0,
    transaction_fees: float = 0.0
) -> dict:
    """
    Calculate dividend distribution efficiency metrics.
    
    Args:
        total_dividend_pool: Total available dividend pool
        distributed_amount: Actually distributed amount
        gas_costs: Blockchain gas costs
        transaction_fees: Transaction processing fees
    
    Returns:
        dict: Distribution efficiency metrics
    """
    total_costs = gas_costs + transaction_fees
    net_distributed = distributed_amount - total_costs
    efficiency_rate = net_distributed / total_dividend_pool if total_dividend_pool > 0 else 0.0
    
    return {
        'total_pool': total_dividend_pool,
        'distributed_amount': distributed_amount,
        'net_distributed': net_distributed,
        'total_costs': total_costs,
        'efficiency_rate': efficiency_rate,
        'cost_percentage': (total_costs / total_dividend_pool) * 100 if total_dividend_pool > 0 else 0.0
    }
```

---

## 📈 **Economic KPIs and Metrics**

### **11. Key Performance Indicators**

```python
def calculate_economic_kpis(
    total_supply: float,
    total_revenue: float,
    dividend_pool: float,
    active_holders: int,
    average_holding_time: float
) -> dict:
    """
    Calculate key economic performance indicators.
    
    Args:
        total_supply: Total ARX supply
        total_revenue: Platform revenue
        dividend_pool: Dividend pool amount
        active_holders: Number of active token holders
        average_holding_time: Average holding time in days
    
    Returns:
        dict: Economic KPIs
    """
    # Dividend yield
    dividend_yield = (dividend_pool / total_supply) * 100 if total_supply > 0 else 0.0
    
    # Revenue per token
    revenue_per_token = total_revenue / total_supply if total_supply > 0 else 0.0
    
    # Holder concentration
    avg_tokens_per_holder = total_supply / active_holders if active_holders > 0 else 0.0
    
    # Velocity (tokens traded per day)
    token_velocity = total_supply / average_holding_time if average_holding_time > 0 else 0.0
    
    return {
        'dividend_yield_percentage': dividend_yield,
        'revenue_per_token': revenue_per_token,
        'avg_tokens_per_holder': avg_tokens_per_holder,
        'token_velocity': token_velocity,
        'holder_concentration': avg_tokens_per_holder / total_supply if total_supply > 0 else 0.0
    }
```

---

## 🎯 **Implementation Examples**

### **Example 1: Standard HVAC VAV Object**

```python
# ArxLogic validation results
validation_metrics = {
    'simulation_pass_rate': 0.95,
    'ai_accuracy_rate': 0.92,
    'system_completion_score': 0.88,
    'error_propagation_score': 0.05
}

# Calculate validation score
validation_score = calculate_validation_score(**validation_metrics)
# Result: 0.91

# Calculate ARX mint
complexity_multiplier = get_complexity_multiplier('hvac')
arx_minted = calculate_arx_mint(validation_score, complexity_multiplier)
# Result: 1.365 ARX (1.0 * 0.91 * 1.5)
```

### **Example 2: Dividend Distribution**

```python
# Platform revenue
revenue_data = {
    'api_usage_revenue': 50000.0,
    'data_download_revenue': 75000.0,
    'contractor_service_revenue': 25000.0
}

# Calculate dividend pool
dividend_pool = calculate_revenue_pool(**revenue_data)
# Result: $150,000

# Calculate dividend per token
total_supply = 1000000.0  # 1M ARX
dividend_per_token = calculate_dividend_per_token(dividend_pool, total_supply)
# Result: $0.15 per ARX

# Calculate user dividend
user_balance = 100.0
user_dividend = calculate_user_dividend(user_balance, dividend_per_token)
# Result: $15.00
```

---

## ✅ **Model Validation**

### **Economic Stability Checks**

1. **Supply Growth Rate**: Should not exceed 50% annually
2. **Dividend Yield**: Target 5-15% annual yield
3. **Revenue Per Token**: Should increase over time
4. **Holder Concentration**: No single holder > 10% of supply
5. **Distribution Efficiency**: > 95% of dividend pool distributed

### **Integration Points**

- **ArxLogic Validation**: Direct integration with existing validation scores
- **Revenue Tracking**: Real-time integration with platform revenue streams
- **User Management**: Seamless integration with existing user authentication
- **Database**: Extends existing PostgreSQL schema
- **Monitoring**: Integrates with existing Prometheus/Grafana dashboards

### **Legal Compliance Integration**

- **Securities Law Compliance**: ARX structured as revenue-sharing token, not equity
- **KYC/AML Requirements**: Integration with compliance services for institutional holders
- **Equity Separation**: Clear distinction between ARX tokens and Arxos equity
- **Regulatory Reporting**: Automated reporting for compliance requirements
- **Jurisdiction Handling**: Support for different regulatory requirements by region

This mathematical model provides a comprehensive framework for ARX tokenomics that integrates seamlessly with the existing Arxos infrastructure while maintaining economic stability, transparency, and legal compliance. 