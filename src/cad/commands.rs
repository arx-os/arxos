//! Command system for CAD operations

use crate::cad::data_model::{Point2D, Entity, Line, Circle, Arc, Rectangle, Polyline, LineStyle};
use std::str::FromStr;

/// CAD commands that can be executed
#[derive(Debug, Clone, PartialEq)]
pub enum Command {
    // Drawing commands
    Line(LineCommand),
    Circle(CircleCommand),
    Arc(ArcCommand),
    Rectangle(RectCommand),
    Polyline(PolylineCommand),
    
    // Edit commands
    Move(MoveCommand),
    Copy(CopyCommand),
    Rotate(RotateCommand),
    Scale(ScaleCommand),
    Delete(DeleteCommand),
    Trim(TrimCommand),
    Extend(ExtendCommand),
    
    // View commands
    Zoom(ZoomCommand),
    Pan(PanCommand),
    Fit,
    
    // Layer commands
    Layer(LayerCommand),
    
    // Utility commands
    Undo,
    Redo,
    Save(String),
    Load(String),
    Export(ExportFormat),
    
    // Mode changes
    SetMode(CommandMode),
    
    // System
    Help,
    Quit,
}

/// Current input mode
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CommandMode {
    Command,    // Typing commands
    Draw,       // Drawing mode
    Edit,       // Editing mode
    View,       // View manipulation
    Select,     // Selecting entities
}

/// Line drawing command
#[derive(Debug, Clone, PartialEq)]
pub struct LineCommand {
    pub start: Option<Point2D>,
    pub end: Option<Point2D>,
    pub style: LineStyle,
}

/// Circle drawing command
#[derive(Debug, Clone, PartialEq)]
pub struct CircleCommand {
    pub center: Option<Point2D>,
    pub radius: Option<f64>,
}

/// Arc drawing command
#[derive(Debug, Clone, PartialEq)]
pub struct ArcCommand {
    pub center: Option<Point2D>,
    pub radius: Option<f64>,
    pub start_angle: Option<f64>,
    pub end_angle: Option<f64>,
}

/// Rectangle drawing command
#[derive(Debug, Clone, PartialEq)]
pub struct RectCommand {
    pub corner1: Option<Point2D>,
    pub corner2: Option<Point2D>,
}

/// Polyline drawing command
#[derive(Debug, Clone, PartialEq)]
pub struct PolylineCommand {
    pub points: Vec<Point2D>,
    pub is_closed: bool,
}

/// Move command
#[derive(Debug, Clone, PartialEq)]
pub struct MoveCommand {
    pub base_point: Option<Point2D>,
    pub target_point: Option<Point2D>,
    pub selection: Vec<usize>,  // Entity indices
}

/// Copy command
#[derive(Debug, Clone, PartialEq)]
pub struct CopyCommand {
    pub base_point: Option<Point2D>,
    pub target_point: Option<Point2D>,
    pub selection: Vec<usize>,
}

/// Rotate command
#[derive(Debug, Clone, PartialEq)]
pub struct RotateCommand {
    pub center: Option<Point2D>,
    pub angle: Option<f64>,
    pub selection: Vec<usize>,
}

/// Scale command
#[derive(Debug, Clone, PartialEq)]
pub struct ScaleCommand {
    pub base_point: Option<Point2D>,
    pub factor: Option<f64>,
    pub selection: Vec<usize>,
}

/// Delete command
#[derive(Debug, Clone, PartialEq)]
pub struct DeleteCommand {
    pub selection: Vec<usize>,
}

/// Trim command
#[derive(Debug, Clone, PartialEq)]
pub struct TrimCommand {
    pub cutting_edges: Vec<usize>,
    pub entities_to_trim: Vec<usize>,
}

/// Extend command
#[derive(Debug, Clone, PartialEq)]
pub struct ExtendCommand {
    pub boundary_edges: Vec<usize>,
    pub entities_to_extend: Vec<usize>,
}

/// Zoom command
#[derive(Debug, Clone, PartialEq)]
pub enum ZoomCommand {
    In,
    Out,
    Window(Point2D, Point2D),
    Scale(f64),
}

/// Pan command
#[derive(Debug, Clone, PartialEq)]
pub struct PanCommand {
    pub delta_x: f64,
    pub delta_y: f64,
}

/// Layer operations
#[derive(Debug, Clone, PartialEq)]
pub enum LayerCommand {
    Create(String),
    Delete(String),
    SetActive(String),
    Toggle(String),
    Lock(String),
    Unlock(String),
}

/// Export formats
#[derive(Debug, Clone, PartialEq)]
pub enum ExportFormat {
    Json,
    Dxf,
    Arxos,  // Native Arxos format
}

/// Command parser
pub struct CommandParser {
    current_mode: CommandMode,
    partial_command: Option<Command>,
    input_buffer: String,
}

impl CommandParser {
    pub fn new() -> Self {
        Self {
            current_mode: CommandMode::Command,
            partial_command: None,
            input_buffer: String::new(),
        }
    }
    
    /// Parse user input into a command
    pub fn parse(&mut self, input: &str) -> Result<Option<Command>, ParseError> {
        // Handle partial commands (multi-step input)
        if let Some(partial) = &mut self.partial_command {
            return self.continue_partial_command(partial.clone(), input);
        }
        
        // Parse new command
        let parts: Vec<&str> = input.trim().split_whitespace().collect();
        if parts.is_empty() {
            return Ok(None);
        }
        
        match parts[0].to_lowercase().as_str() {
            // Drawing commands
            "line" | "l" => self.start_line_command(),
            "circle" | "c" => self.start_circle_command(),
            "arc" | "a" => self.start_arc_command(),
            "rectangle" | "rect" | "r" => self.start_rectangle_command(),
            "polyline" | "pl" => self.start_polyline_command(),
            
            // Edit commands
            "move" | "m" => self.start_move_command(),
            "copy" | "cp" => self.start_copy_command(),
            "rotate" | "ro" => self.start_rotate_command(),
            "scale" | "sc" => self.start_scale_command(),
            "delete" | "del" | "d" => self.start_delete_command(),
            
            // View commands
            "zoom" | "z" => self.parse_zoom_command(&parts[1..]),
            "pan" | "p" => self.parse_pan_command(&parts[1..]),
            "fit" | "f" => Ok(Some(Command::Fit)),
            
            // Layer commands
            "layer" | "la" => self.parse_layer_command(&parts[1..]),
            
            // Utility commands
            "undo" | "u" => Ok(Some(Command::Undo)),
            "redo" => Ok(Some(Command::Redo)),
            "save" | "s" => self.parse_save_command(&parts[1..]),
            "load" | "o" => self.parse_load_command(&parts[1..]),
            "export" | "e" => self.parse_export_command(&parts[1..]),
            
            // System commands
            "help" | "h" | "?" => Ok(Some(Command::Help)),
            "quit" | "q" | "exit" => Ok(Some(Command::Quit)),
            
            _ => Err(ParseError::UnknownCommand(parts[0].to_string())),
        }
    }
    
    /// Start line command (multi-step)
    fn start_line_command(&mut self) -> Result<Option<Command>, ParseError> {
        self.partial_command = Some(Command::Line(LineCommand {
            start: None,
            end: None,
            style: LineStyle::Solid,
        }));
        Ok(None)  // Waiting for more input
    }
    
    /// Start circle command
    fn start_circle_command(&mut self) -> Result<Option<Command>, ParseError> {
        self.partial_command = Some(Command::Circle(CircleCommand {
            center: None,
            radius: None,
        }));
        Ok(None)
    }
    
    /// Start arc command
    fn start_arc_command(&mut self) -> Result<Option<Command>, ParseError> {
        self.partial_command = Some(Command::Arc(ArcCommand {
            center: None,
            radius: None,
            start_angle: None,
            end_angle: None,
        }));
        Ok(None)
    }
    
    /// Start rectangle command
    fn start_rectangle_command(&mut self) -> Result<Option<Command>, ParseError> {
        self.partial_command = Some(Command::Rectangle(RectCommand {
            corner1: None,
            corner2: None,
        }));
        Ok(None)
    }
    
    /// Start polyline command
    fn start_polyline_command(&mut self) -> Result<Option<Command>, ParseError> {
        self.partial_command = Some(Command::Polyline(PolylineCommand {
            points: Vec::new(),
            is_closed: false,
        }));
        Ok(None)
    }
    
    /// Continue partial command with new input
    fn continue_partial_command(&mut self, mut cmd: Command, input: &str) -> Result<Option<Command>, ParseError> {
        match &mut cmd {
            Command::Line(ref mut line_cmd) => {
                if line_cmd.start.is_none() {
                    line_cmd.start = Some(self.parse_point(input)?);
                    self.partial_command = Some(cmd);
                    Ok(None)
                } else if line_cmd.end.is_none() {
                    line_cmd.end = Some(self.parse_point(input)?);
                    self.partial_command = None;
                    Ok(Some(cmd))
                } else {
                    Ok(None)
                }
            }
            Command::Circle(ref mut circle_cmd) => {
                if circle_cmd.center.is_none() {
                    circle_cmd.center = Some(self.parse_point(input)?);
                    self.partial_command = Some(cmd);
                    Ok(None)
                } else if circle_cmd.radius.is_none() {
                    circle_cmd.radius = Some(self.parse_number(input)?);
                    self.partial_command = None;
                    Ok(Some(cmd))
                } else {
                    Ok(None)
                }
            }
            // Add other command continuations...
            _ => Ok(None),
        }
    }
    
    /// Parse point from string (e.g., "10,20" or "10 20")
    fn parse_point(&self, input: &str) -> Result<Point2D, ParseError> {
        let coords: Vec<&str> = input
            .split(|c| c == ',' || c == ' ')
            .filter(|s| !s.is_empty())
            .collect();
        
        if coords.len() != 2 {
            return Err(ParseError::InvalidPoint(input.to_string()));
        }
        
        let x = coords[0].parse::<f64>()
            .map_err(|_| ParseError::InvalidNumber(coords[0].to_string()))?;
        let y = coords[1].parse::<f64>()
            .map_err(|_| ParseError::InvalidNumber(coords[1].to_string()))?;
        
        Ok(Point2D { x, y })
    }
    
    /// Parse number from string
    fn parse_number(&self, input: &str) -> Result<f64, ParseError> {
        input.parse::<f64>()
            .map_err(|_| ParseError::InvalidNumber(input.to_string()))
    }
    
    // Stub implementations for other commands
    fn start_move_command(&mut self) -> Result<Option<Command>, ParseError> {
        Ok(None)
    }
    
    fn start_copy_command(&mut self) -> Result<Option<Command>, ParseError> {
        Ok(None)
    }
    
    fn start_rotate_command(&mut self) -> Result<Option<Command>, ParseError> {
        Ok(None)
    }
    
    fn start_scale_command(&mut self) -> Result<Option<Command>, ParseError> {
        Ok(None)
    }
    
    fn start_delete_command(&mut self) -> Result<Option<Command>, ParseError> {
        Ok(None)
    }
    
    fn parse_zoom_command(&self, args: &[&str]) -> Result<Option<Command>, ParseError> {
        if args.is_empty() {
            return Ok(Some(Command::Zoom(ZoomCommand::In)));
        }
        
        match args[0] {
            "in" | "i" => Ok(Some(Command::Zoom(ZoomCommand::In))),
            "out" | "o" => Ok(Some(Command::Zoom(ZoomCommand::Out))),
            _ => {
                if let Ok(scale) = args[0].parse::<f64>() {
                    Ok(Some(Command::Zoom(ZoomCommand::Scale(scale))))
                } else {
                    Err(ParseError::InvalidArgument(args[0].to_string()))
                }
            }
        }
    }
    
    fn parse_pan_command(&self, args: &[&str]) -> Result<Option<Command>, ParseError> {
        if args.len() != 2 {
            return Err(ParseError::InvalidArgumentCount(2, args.len()));
        }
        
        let dx = self.parse_number(args[0])?;
        let dy = self.parse_number(args[1])?;
        
        Ok(Some(Command::Pan(PanCommand {
            delta_x: dx,
            delta_y: dy,
        })))
    }
    
    fn parse_layer_command(&self, args: &[&str]) -> Result<Option<Command>, ParseError> {
        if args.is_empty() {
            return Err(ParseError::MissingArgument("layer operation".to_string()));
        }
        
        match args[0] {
            "create" | "new" if args.len() > 1 => {
                Ok(Some(Command::Layer(LayerCommand::Create(args[1].to_string()))))
            }
            "delete" | "del" if args.len() > 1 => {
                Ok(Some(Command::Layer(LayerCommand::Delete(args[1].to_string()))))
            }
            "active" | "set" if args.len() > 1 => {
                Ok(Some(Command::Layer(LayerCommand::SetActive(args[1].to_string()))))
            }
            _ => Err(ParseError::InvalidArgument(args[0].to_string())),
        }
    }
    
    fn parse_save_command(&self, args: &[&str]) -> Result<Option<Command>, ParseError> {
        if args.is_empty() {
            Ok(Some(Command::Save("drawing.arxos".to_string())))
        } else {
            Ok(Some(Command::Save(args[0].to_string())))
        }
    }
    
    fn parse_load_command(&self, args: &[&str]) -> Result<Option<Command>, ParseError> {
        if args.is_empty() {
            return Err(ParseError::MissingArgument("filename".to_string()));
        }
        Ok(Some(Command::Load(args[0].to_string())))
    }
    
    fn parse_export_command(&self, args: &[&str]) -> Result<Option<Command>, ParseError> {
        if args.is_empty() {
            return Ok(Some(Command::Export(ExportFormat::Arxos)));
        }
        
        match args[0] {
            "json" => Ok(Some(Command::Export(ExportFormat::Json))),
            "dxf" => Ok(Some(Command::Export(ExportFormat::Dxf))),
            "arxos" => Ok(Some(Command::Export(ExportFormat::Arxos))),
            _ => Err(ParseError::InvalidArgument(args[0].to_string())),
        }
    }
    
    /// Get prompt for current partial command
    pub fn get_prompt(&self) -> String {
        match &self.partial_command {
            Some(Command::Line(cmd)) => {
                if cmd.start.is_none() {
                    "Line: First point (x,y): ".to_string()
                } else {
                    "Line: Second point (x,y): ".to_string()
                }
            }
            Some(Command::Circle(cmd)) => {
                if cmd.center.is_none() {
                    "Circle: Center point (x,y): ".to_string()
                } else {
                    "Circle: Radius: ".to_string()
                }
            }
            _ => "Command: ".to_string(),
        }
    }
}

/// Parse errors
#[derive(Debug, Clone)]
pub enum ParseError {
    UnknownCommand(String),
    InvalidPoint(String),
    InvalidNumber(String),
    InvalidArgument(String),
    InvalidArgumentCount(usize, usize),  // expected, actual
    MissingArgument(String),
}