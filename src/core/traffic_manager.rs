#![forbid(unsafe_code)]
#![deny(clippy::unwrap_used, clippy::expect_used, clippy::pedantic, clippy::nursery)]
#![cfg_attr(test, allow(clippy::unwrap_used, clippy::expect_used))]
#![allow(clippy::module_name_repetitions)]
use std::collections::{HashMap, VecDeque};
use std::time::{Duration, Instant};

/// Traffic management for ArxOS mesh network
/// Implements TDMA, anti-congestion, and fair queuing
pub struct TrafficManager {
    pub time_slots: TimeSlotSchedule,
    pub queues: ServiceQueues,
    pub congestion_detector: CongestionDetector,
    pub bandwidth_allocator: DynamicBandwidthAllocator,
}

/// Time Division Multiple Access (TDMA) scheduler
pub struct TimeSlotSchedule {
    pub slot_duration_ms: u32,
    pub slots_per_frame: u32,
    pub current_slot: u32,
    pub service_assignments: HashMap<ServiceType, SlotRange>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ServiceType {
    Emergency,      // Always gets slots 0-99
    ArxOSCore,     // Building intelligence
    Educational,    // School content
    Environmental,  // Sensors
    Municipal,      // City services
    Financial,      // Banking (NOT HFT!)
    Commercial,     // Everything else
}

#[derive(Debug, Clone)]
pub struct SlotRange {
    pub start: u32,
    pub end: u32,
    pub priority: Priority,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Priority {
    Critical = 0,
    High = 1,
    Medium = 2,
    Low = 3,
    BestEffort = 4,
}

impl TimeSlotSchedule {
    pub fn new() -> Self {
        let mut assignments = HashMap::new();
        
        // 1 second = 1000ms = 1000 slots
        assignments.insert(ServiceType::Emergency, SlotRange {
            start: 0,
            end: 99,
            priority: Priority::Critical,
        });
        
        assignments.insert(ServiceType::ArxOSCore, SlotRange {
            start: 100,
            end: 299,
            priority: Priority::High,
        });
        
        assignments.insert(ServiceType::Educational, SlotRange {
            start: 300,
            end: 499,
            priority: Priority::Medium,
        });
        
        assignments.insert(ServiceType::Environmental, SlotRange {
            start: 500,
            end: 599,
            priority: Priority::Medium,
        });
        
        assignments.insert(ServiceType::Municipal, SlotRange {
            start: 600,
            end: 699,
            priority: Priority::Low,
        });
        
        assignments.insert(ServiceType::Financial, SlotRange {
            start: 700,
            end: 799,
            priority: Priority::Low,
        });
        
        assignments.insert(ServiceType::Commercial, SlotRange {
            start: 800,
            end: 999,
            priority: Priority::BestEffort,
        });
        
        Self {
            slot_duration_ms: 1,
            slots_per_frame: 1000,
            current_slot: 0,
            service_assignments: assignments,
        }
    }
    
    pub fn can_transmit(&self, service: ServiceType) -> bool {
        if let Some(range) = self.service_assignments.get(&service) {
            self.current_slot >= range.start && self.current_slot <= range.end
        } else {
            false
        }
    }
    
    pub fn advance_slot(&mut self) {
        self.current_slot = (self.current_slot + 1) % self.slots_per_frame;
    }
}

/// Per-service packet queues with fair queuing
pub struct ServiceQueues {
    queues: HashMap<ServiceType, PacketQueue>,
    max_packet_size: usize,
    anti_starvation_timeout: Duration,
}

pub struct PacketQueue {
    packets: VecDeque<QueuedPacket>,
    max_depth: usize,
    total_bytes: usize,
    oldest_packet_time: Option<Instant>,
}

pub struct QueuedPacket {
    pub data: Vec<u8>,
    pub enqueued_at: Instant,
    pub attempts: u32,
    pub service_type: ServiceType,
}

impl ServiceQueues {
    pub fn new() -> Self {
        let mut queues = HashMap::new();
        
        // Different queue depths for different services
        queues.insert(ServiceType::Emergency, PacketQueue::new(1000));
        queues.insert(ServiceType::ArxOSCore, PacketQueue::new(500));
        queues.insert(ServiceType::Educational, PacketQueue::new(2000));
        queues.insert(ServiceType::Environmental, PacketQueue::new(300));
        queues.insert(ServiceType::Municipal, PacketQueue::new(300));
        queues.insert(ServiceType::Financial, PacketQueue::new(400));
        queues.insert(ServiceType::Commercial, PacketQueue::new(200));
        
        Self {
            queues,
            max_packet_size: 65536, // 64KB max
            anti_starvation_timeout: Duration::from_secs(30),
        }
    }
    
    pub fn enqueue(&mut self, packet: Vec<u8>, service: ServiceType) -> Result<(), String> {
        // Enforce packet size limit to prevent channel hogging
        if packet.len() > self.max_packet_size {
            return Err("Packet too large - must chunk".to_string());
        }
        
        if let Some(queue) = self.queues.get_mut(&service) {
            queue.push(QueuedPacket {
                data: packet,
                enqueued_at: Instant::now(),
                attempts: 0,
                service_type: service,
            })
        } else {
            Err("Unknown service type".to_string())
        }
    }
    
    pub fn get_next_packet(&mut self, current_slot: u32, schedule: &TimeSlotSchedule) -> Option<Vec<u8>> {
        // Bound work per call to avoid starvation of other tasks
        const MAX_SCANS_PER_CALL: usize = 32;
        let mut scanned = 0usize;
        // First check for starving packets
        for (_service, queue) in &mut self.queues {
            if scanned >= MAX_SCANS_PER_CALL { break; }
            if let Some(age) = queue.age_of_oldest() {
                if age > self.anti_starvation_timeout {
                    // Anti-starvation override
                    return queue.pop().map(|p| p.data);
                }
            }
            scanned += 1;
        }
        
        // Normal TDMA scheduling
        for (service, range) in &schedule.service_assignments {
            if current_slot >= range.start && current_slot <= range.end {
                if let Some(queue) = self.queues.get_mut(service) {
                    return queue.pop().map(|p| p.data);
                }
            }
        }
        
        None
    }
}

impl PacketQueue {
    pub fn new(max_depth: usize) -> Self {
        Self {
            packets: VecDeque::new(),
            max_depth,
            total_bytes: 0,
            oldest_packet_time: None,
        }
    }
    
    pub fn push(&mut self, packet: QueuedPacket) -> Result<(), String> {
        if self.packets.len() >= self.max_depth {
            return Err("Queue full".to_string());
        }
        
        self.total_bytes += packet.data.len();
        
        if self.oldest_packet_time.is_none() {
            self.oldest_packet_time = Some(packet.enqueued_at);
        }
        
        self.packets.push_back(packet);
        Ok(())
    }
    
    pub fn pop(&mut self) -> Option<QueuedPacket> {
        if let Some(packet) = self.packets.pop_front() {
            self.total_bytes -= packet.data.len();
            
            if self.packets.is_empty() {
                self.oldest_packet_time = None;
            } else {
                self.oldest_packet_time = self.packets.front().map(|p| p.enqueued_at);
            }
            
            Some(packet)
        } else {
            None
        }
    }
    
    pub fn age_of_oldest(&self) -> Option<Duration> {
        self.oldest_packet_time.map(|t| t.elapsed())
    }
}

/// Congestion detection and response
pub struct CongestionDetector {
    pub queue_depth_threshold: f32,  // 80% = congestion
    pub latency_multiplier: f32,     // 2x normal = congestion
    pub retransmit_threshold: f32,   // 5% = congestion
    pub channel_usage_threshold: f32, // 90% = congestion
    
    pub current_metrics: CongestionMetrics,
}

pub struct CongestionMetrics {
    pub queue_depth_percent: f32,
    pub average_latency_ms: f32,
    pub retransmit_rate: f32,
    pub channel_utilization: f32,
}

impl CongestionDetector {
    pub fn is_congested(&self) -> bool {
        self.current_metrics.queue_depth_percent > self.queue_depth_threshold ||
        self.current_metrics.average_latency_ms > 1000.0 * self.latency_multiplier ||
        self.current_metrics.retransmit_rate > self.retransmit_threshold ||
        self.current_metrics.channel_utilization > self.channel_usage_threshold
    }
    
    pub fn get_congestion_response(&self) -> CongestionResponse {
        if !self.is_congested() {
            return CongestionResponse::Normal;
        }
        
        // Graduated response based on severity
        let severity = self.calculate_severity();
        
        match severity {
            0..=30 => CongestionResponse::ReducePacketSize,
            31..=60 => CongestionResponse::IncreaseInterPacketGap,
            61..=80 => CongestionResponse::ActivateBackupPaths,
            81..=100 => CongestionResponse::EmergencyPrioritization,
            _ => CongestionResponse::Normal,
        }
    }
    
    fn calculate_severity(&self) -> u32 {
        let metrics = &self.current_metrics;
        let severity = (
            (metrics.queue_depth_percent / self.queue_depth_threshold * 25.0) +
            (metrics.average_latency_ms / (1000.0 * self.latency_multiplier) * 25.0) +
            (metrics.retransmit_rate / self.retransmit_threshold * 25.0) +
            (metrics.channel_utilization / self.channel_usage_threshold * 25.0)
        ) as u32;
        
        severity.min(100)
    }
}

pub enum CongestionResponse {
    Normal,
    ReducePacketSize,
    IncreaseInterPacketGap,
    ActivateBackupPaths,
    EmergencyPrioritization,
}

/// Dynamic bandwidth allocation based on actual usage
pub struct DynamicBandwidthAllocator {
    pub service_allocations: HashMap<ServiceType, BandwidthAllocation>,
    pub total_bandwidth_kbps: u32,
    pub overnight_mode: bool,
    pub emergency_override: bool,
}

pub struct BandwidthAllocation {
    pub guaranteed_kbps: u32,
    pub maximum_kbps: u32,
    pub current_usage_kbps: u32,
    pub priority: Priority,
}

impl DynamicBandwidthAllocator {
    pub fn new(total_bandwidth_kbps: u32) -> Self {
        let mut allocations = HashMap::new();
        
        // Normal daytime allocations
        allocations.insert(ServiceType::Emergency, BandwidthAllocation {
            guaranteed_kbps: 50,  // Always reserved
            maximum_kbps: total_bandwidth_kbps, // Can take everything
            current_usage_kbps: 0,
            priority: Priority::Critical,
        });
        
        allocations.insert(ServiceType::ArxOSCore, BandwidthAllocation {
            guaranteed_kbps: 100,
            maximum_kbps: 200,
            current_usage_kbps: 0,
            priority: Priority::High,
        });
        
        allocations.insert(ServiceType::Educational, BandwidthAllocation {
            guaranteed_kbps: 150,
            maximum_kbps: 300,
            current_usage_kbps: 0,
            priority: Priority::Medium,
        });
        
        allocations.insert(ServiceType::Financial, BandwidthAllocation {
            guaranteed_kbps: 20,  // NOT for HFT!
            maximum_kbps: 50,     // Offline payments only
            current_usage_kbps: 0,
            priority: Priority::Low,
        });
        
        Self {
            service_allocations: allocations,
            total_bandwidth_kbps,
            overnight_mode: false,
            emergency_override: false,
        }
    }
    
    pub fn set_overnight_mode(&mut self, enabled: bool) {
        self.overnight_mode = enabled;
        
        if enabled {
            // Schools get everything overnight for bulk transfers
            if let Some(edu) = self.service_allocations.get_mut(&ServiceType::Educational) {
                edu.maximum_kbps = self.total_bandwidth_kbps;
            }
        } else {
            // Return to normal limits
            if let Some(edu) = self.service_allocations.get_mut(&ServiceType::Educational) {
                edu.maximum_kbps = 300;
            }
        }
    }
    
    pub fn activate_emergency(&mut self) {
        self.emergency_override = true;
        
        // Emergency gets everything, others get minimums
        for (service, alloc) in &mut self.service_allocations {
            if *service == ServiceType::Emergency {
                alloc.maximum_kbps = self.total_bandwidth_kbps;
            } else {
                alloc.maximum_kbps = alloc.guaranteed_kbps;
            }
        }
    }
}

/// Multi-path routing to prevent highway effect
pub struct MultiPathRouter {
    pub paths: Vec<RoutePath>,
    pub load_balancer: LoadBalancer,
    pub path_metrics: HashMap<PathId, PathMetrics>,
}

pub struct RoutePath {
    pub path_id: PathId,
    pub hops: Vec<NodeId>,
    pub total_latency_ms: u32,
    pub available_bandwidth_kbps: u32,
    pub reliability_score: f32,
}

pub type PathId = u32;
pub type NodeId = [u8; 4];

pub struct PathMetrics {
    pub packets_sent: u64,
    pub packets_lost: u64,
    pub average_latency_ms: f32,
    pub jitter_ms: f32,
}

pub struct LoadBalancer {
    pub strategy: LoadBalancingStrategy,
    pub path_weights: HashMap<PathId, f32>,
    pub rr_index: usize,
}

pub enum LoadBalancingStrategy {
    RoundRobin,
    WeightedRandom,
    LeastLatency,
    MaxBandwidth,
    AdaptiveQuality,
}

impl MultiPathRouter {
    pub fn select_path(&mut self, packet_size: usize, service: ServiceType) -> PathId {
        match service {
            ServiceType::Emergency => {
                // Always use most reliable path for emergency
                self.most_reliable_path()
            },
            ServiceType::Financial => {
                // Financial needs reliability over speed (NOT HFT!)
                // This is for offline payments, not trading
                self.most_reliable_path()
            },
            ServiceType::Educational if self.is_bulk_transfer(packet_size) => {
                // Bulk transfers spread across all paths
                self.load_balanced_path()
            },
            _ => {
                // Normal traffic uses adaptive routing
                self.adaptive_path_selection(packet_size)
            }
        }
    }
    
    fn most_reliable_path(&self) -> PathId {
        self.paths
            .iter()
            .max_by(|a, b| a.reliability_score.partial_cmp(&b.reliability_score).unwrap_or(std::cmp::Ordering::Equal))
            .map(|p| p.path_id)
            .unwrap_or(0)
    }
    
    fn load_balanced_path(&mut self) -> PathId {
        self.load_balancer.next_path(&self.paths)
    }
    
    fn adaptive_path_selection(&self, packet_size: usize) -> PathId {
        // Consider latency, bandwidth, and reliability
        self.paths
            .iter()
            .filter(|p| p.available_bandwidth_kbps as usize * 1000 / 8 > packet_size)
            .min_by_key(|p| p.total_latency_ms)
            .map(|p| p.path_id)
            .unwrap_or(0)
    }
    
    fn is_bulk_transfer(&self, packet_size: usize) -> bool {
        packet_size > 10000 // 10KB+ considered bulk
    }
}

impl LoadBalancer {
    pub fn next_path(&mut self, paths: &[RoutePath]) -> PathId {
        match self.strategy {
            LoadBalancingStrategy::RoundRobin => {
                if paths.is_empty() { return 0; }
                let id = paths[self.rr_index % paths.len()].path_id;
                self.rr_index = (self.rr_index + 1) % paths.len();
                id
            },
            LoadBalancingStrategy::WeightedRandom => {
                // Weighted by available bandwidth
                let total_weight: f32 = paths.iter()
                    .map(|p| p.available_bandwidth_kbps as f32)
                    .sum();
                
                let mut random = rand::random::<f32>() * total_weight;
                
                for path in paths {
                    random -= path.available_bandwidth_kbps as f32;
                    if random <= 0.0 {
                        return path.path_id;
                    }
                }
                
                paths[0].path_id
            },
            _ => paths[0].path_id,
        }
    }
}

// Dummy rand function for example
mod rand {
    pub fn random<T>() -> T 
    where 
        T: Default 
    {
        T::default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_tdma_scheduling() {
        let mut schedule = TimeSlotSchedule::new();
        
        // Emergency always gets slots 0-99
        schedule.current_slot = 50;
        assert!(schedule.can_transmit(ServiceType::Emergency));
        assert!(!schedule.can_transmit(ServiceType::Educational));
        
        // Educational gets slots 300-499
        schedule.current_slot = 400;
        assert!(!schedule.can_transmit(ServiceType::Emergency));
        assert!(schedule.can_transmit(ServiceType::Educational));
    }
    
    #[test]
    fn test_overnight_mode() {
        let mut allocator = DynamicBandwidthAllocator::new(500);
        
        // Normal mode - educational limited
        assert_eq!(
            allocator.service_allocations[&ServiceType::Educational].maximum_kbps,
            300
        );
        
        // Overnight mode - educational gets everything
        allocator.set_overnight_mode(true);
        assert_eq!(
            allocator.service_allocations[&ServiceType::Educational].maximum_kbps,
            500
        );
    }
    
    #[test]
    fn test_financial_is_not_hft() {
        // This test documents that financial services are NOT for HFT
        let allocator = DynamicBandwidthAllocator::new(500);
        
        // Financial gets minimal bandwidth - it's for offline payments only
        let financial = &allocator.service_allocations[&ServiceType::Financial];
        assert_eq!(financial.guaranteed_kbps, 20); // Tiny allocation
        assert_eq!(financial.maximum_kbps, 50);     // Can't burst much
        assert_eq!(financial.priority, Priority::Low); // Low priority
        
        // This is by design - we're 2,000,000x too slow for HFT
    }

    #[test]
    fn test_round_robin_deterministic() {
        let mut lb = LoadBalancer { strategy: LoadBalancingStrategy::RoundRobin, path_weights: HashMap::new(), rr_index: 0 };
        let paths = vec![
            RoutePath { path_id: 1, hops: vec![], total_latency_ms: 10, available_bandwidth_kbps: 10, reliability_score: 0.9 },
            RoutePath { path_id: 2, hops: vec![], total_latency_ms: 20, available_bandwidth_kbps: 20, reliability_score: 0.8 },
            RoutePath { path_id: 3, hops: vec![], total_latency_ms: 30, available_bandwidth_kbps: 30, reliability_score: 0.7 },
        ];
        let seq: Vec<_> = (0..6).map(|_| lb.next_path(&paths)).collect();
        assert_eq!(seq, vec![1,2,3,1,2,3]);
    }
}