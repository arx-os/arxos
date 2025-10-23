use uniffi;

#[derive(Debug, Clone)]
pub struct MobileRoom {
    pub id: String,
    pub name: String,
    pub floor: i32,
    pub wing: String,
    pub room_type: String,
}

#[derive(Debug, Clone)]
pub struct MobileEquipment {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub status: String,
    pub location: String,
    pub room_id: String,
}

#[derive(Debug, Clone)]
pub struct GitStatus {
    pub branch: String,
    pub commit_count: i32,
    pub last_commit: String,
    pub has_changes: bool,
}

#[derive(Debug, Clone)]
pub struct CommandResult {
    pub success: bool,
    pub output: String,
    pub error: String,
}

pub fn hello_world() -> String {
    "Hello from ArxOS Mobile!".to_string()
}

pub fn create_room(name: String, floor: i32, wing: String) -> MobileRoom {
    MobileRoom {
        id: format!("room-{}", name),
        name,
        floor,
        wing,
        room_type: "classroom".to_string(),
    }
}

pub fn get_rooms() -> Vec<MobileRoom> {
    vec![
        MobileRoom {
            id: "room-1".to_string(),
            name: "Math Classroom".to_string(),
            floor: 1,
            wing: "A".to_string(),
            room_type: "classroom".to_string(),
        },
        MobileRoom {
            id: "room-2".to_string(),
            name: "Science Lab".to_string(),
            floor: 2,
            wing: "B".to_string(),
            room_type: "laboratory".to_string(),
        },
    ]
}

pub fn add_equipment(name: String, equipment_type: String, room_id: String) -> MobileEquipment {
    MobileEquipment {
        id: format!("eq-{}", name),
        name,
        equipment_type,
        status: "active".to_string(),
        location: "room".to_string(),
        room_id,
    }
}

pub fn get_equipment() -> Vec<MobileEquipment> {
    vec![
        MobileEquipment {
            id: "eq-1".to_string(),
            name: "HVAC Unit".to_string(),
            equipment_type: "hvac".to_string(),
            status: "active".to_string(),
            location: "room".to_string(),
            room_id: "room-1".to_string(),
        },
    ]
}

pub fn get_git_status() -> GitStatus {
    GitStatus {
        branch: "main".to_string(),
        commit_count: 42,
        last_commit: "Initial commit".to_string(),
        has_changes: false,
    }
}

pub fn execute_command(command: String) -> CommandResult {
    match command.as_str() {
        "status" => CommandResult {
            success: true,
            output: "Repository status: clean".to_string(),
            error: String::new(),
        },
        "rooms" => CommandResult {
            success: true,
            output: "Math Classroom (Floor 1)\nScience Lab (Floor 2)".to_string(),
            error: String::new(),
        },
        "equipment" => CommandResult {
            success: true,
            output: "HVAC Unit - hvac (active)".to_string(),
            error: String::new(),
        },
        _ => CommandResult {
            success: false,
            output: String::new(),
            error: format!("Unknown command: {}", command),
        },
    }
}

uniffi::include_scaffolding!("arxos_mobile");