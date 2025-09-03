//! Player state management

/// Player state in the game world
#[derive(Debug, Clone)]
pub struct Player {
    pub id: u32,
    pub name: String,
    pub position: (u16, u16, u16),
    pub health: u8,
    pub inventory: Vec<String>,
}

impl Player {
    pub fn new(id: u32, name: String) -> Self {
        Self {
            id,
            name,
            position: (0, 0, 0),
            health: 100,
            inventory: Vec::new(),
        }
    }
}

/// Player state enum
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum PlayerState {
    Idle,
    Moving,
    Examining,
    Reporting,
}