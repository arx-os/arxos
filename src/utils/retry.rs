//! Retry logic utilities for resilient operations

use std::time::Duration;
use std::fmt::Debug;

/// Retry configuration
#[derive(Debug, Clone)]
pub struct RetryConfig {
    /// Maximum number of retry attempts
    pub max_attempts: usize,
    /// Initial delay between retries
    pub initial_delay: Duration,
    /// Multiplier for exponential backoff
    pub backoff_multiplier: f64,
    /// Maximum delay between retries
    pub max_delay: Duration,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_attempts: 3,
            initial_delay: Duration::from_millis(100),
            backoff_multiplier: 2.0,
            max_delay: Duration::from_secs(5),
        }
    }
}

/// Retry a fallible operation with exponential backoff
pub fn retry<F, T, E>(config: &RetryConfig, mut operation: F) -> Result<T, E>
where
    F: FnMut() -> Result<T, E>,
    E: Debug,
{
    let mut delay = config.initial_delay;
    let mut last_error = None;
    
    for attempt in 0..config.max_attempts {
        match operation() {
            Ok(result) => return Ok(result),
            Err(e) => {
                last_error = Some(e);
                
                // Don't delay after the last attempt
                if attempt < config.max_attempts - 1 {
                    std::thread::sleep(delay);
                    
                    // Calculate next delay with exponential backoff
                    let next_delay_secs = delay.as_secs_f64() * config.backoff_multiplier;
                    let next_delay = Duration::from_secs_f64(next_delay_secs);
                    
                    // Cap at max delay
                    delay = if next_delay > config.max_delay {
                        config.max_delay
                    } else {
                        next_delay
                    };
                }
            }
        }
    }
    
    // Last attempt failed, return the last error
    Err(last_error.unwrap())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_retry_success_first_attempt() {
        let config = RetryConfig::default();
        let result = retry(&config, || Ok::<i32, &str>(42));
        assert_eq!(result, Ok(42));
    }
    
    #[test]
    fn test_retry_success_on_second_attempt() {
        let config = RetryConfig::default();
        let mut attempts = 0;
        let result = retry(&config, || {
            attempts += 1;
            if attempts < 2 {
                Err("failed")
            } else {
                Ok(42)
            }
        });
        assert_eq!(result, Ok(42));
        assert_eq!(attempts, 2);
    }
    
    #[test]
    fn test_retry_exhausts_attempts() {
        let config = RetryConfig {
            max_attempts: 3,
            initial_delay: Duration::from_millis(1),
            backoff_multiplier: 2.0,
            max_delay: Duration::from_secs(5),
        };
        let result = retry(&config, || Err::<i32, &str>("always fails"));
        assert_eq!(result, Err("always fails"));
    }
}

