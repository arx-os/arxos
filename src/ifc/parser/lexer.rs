//! STEP-21 Lexer implementation for high-speed IFC parsing.
//! 
//! This module implements a streamlined ISO-10303-21 lexer optimized for 
//! large BIM datasets. It avoids complex parser combinators for maximum 
//! throughput and memory efficiency.

use std::str::FromStr;

/// A raw entity extracted from a STEP-21 DATA section.
#[derive(Debug, Clone, PartialEq)]
pub struct RawEntity {
    /// The STEP ID (e.g., 123 from #123)
    pub id: u64,
    /// The IFC class name (e.g., "IFCSPACE")
    pub class: String,
    /// The raw parameters associated with the entity
    pub params: Vec<Param>,
}

/// A parameter value in a STEP-21 entity definition.
#[derive(Debug, Clone, PartialEq)]
pub enum Param {
    /// Integer value (e.g., 42, -5)
    Integer(i64),
    /// Floating point value (e.g., 10.5, -2.3e10)
    Float(f64),
    /// STEP string value (e.g., 'Room Name')
    String(String),
    /// STEP reference to another entity (e.g., #10)
    Reference(u64),
    /// Nested list of parameters (e.g., (1, (2, 3), 4))
    List(Vec<Param>),
    /// Null/Omitted parameter ($)
    Null,
    /// Enumeration value (e.g., .INTERNAL.)
    Enum(String),
    /// Boolean value (e.g., .T., .F. or .U.)
    Boolean(bool),
    /// Typed value (e.g., IFCLABEL('Main Office'))
    Typed(String, Box<Param>),
}

/// Lexer for STEP-21 files.
pub struct StepLexer {
    /// The full input content of the IFC file
    input: Vec<char>,
    /// Current position in the input
    pos: usize,
}

impl StepLexer {
    /// Create a new lexer from a string slice.
    pub fn new(input: &str) -> Self {
        Self {
            input: input.chars().collect(),
            pos: 0,
        }
    }

    /// Reset the lexer to a specific position (useful for lazy loading).
    pub fn seek(&mut self, offset: usize) {
        self.pos = offset;
    }

    /// Parse the next entity from the current position.
    /// 
    /// Returns None if no more entities are found.
    pub fn next_entity(&mut self) -> Option<RawEntity> {
        // Skip until we find the start of an entity (#)
        self.skip_to_entity_start()?;

        // 1. Read the ID (#123)
        self.pos += 1; // skip #
        let id_str = self.read_while(|c| c.is_ascii_digit());
        let id = u64::from_str(&id_str).ok()?;

        // 2. Skip to '='
        self.skip_whitespace();
        if self.peek() != Some('=') {
            return None;
        }
        self.pos += 1; // skip =
        self.skip_whitespace();

        // 3. Read Class Name (e.g., IFCSPACE)
        let class = self.read_while(|c| c.is_ascii_alphanumeric() || c == '_');
        
        // 4. Read Parameters (...)
        self.skip_whitespace();
        let params = if self.peek() == Some('(') {
            self.parse_param_list().unwrap_or_default()
        } else {
            Vec::new()
        };

        // 5. Skip semicolon
        self.skip_whitespace();
        if self.peek() == Some(';') {
            self.pos += 1;
        }

        Some(RawEntity { id, class, params })
    }

    // --- Helper Methods ---

    fn skip_to_entity_start(&mut self) -> Option<()> {
        while self.pos < self.input.len() {
            if self.input[self.pos] == '#' {
                return Some(());
            }
            self.pos += 1;
        }
        None
    }

    fn skip_whitespace(&mut self) {
        while self.pos < self.input.len() && self.input[self.pos].is_whitespace() {
            self.pos += 1;
        }
    }

    fn peek(&self) -> Option<char> {
        self.input.get(self.pos).copied()
    }

    fn read_while<F>(&mut self, f: F) -> String 
    where F: Fn(char) -> bool {
        let mut result = String::new();
        while self.pos < self.input.len() && f(self.input[self.pos]) {
            result.push(self.input[self.pos]);
            self.pos += 1;
        }
        result
    }

    fn parse_param_list(&mut self) -> Option<Vec<Param>> {
        self.pos += 1; // skip (
        let mut params = Vec::new();

        while self.pos < self.input.len() {
            self.skip_whitespace();
            
            if self.peek() == Some(')') {
                self.pos += 1;
                return Some(params);
            }

            if let Some(param) = self.parse_single_param() {
                params.push(param);
            }

            self.skip_whitespace();
            if self.peek() == Some(',') {
                self.pos += 1;
            }
        }
        None
    }

    fn parse_single_param(&mut self) -> Option<Param> {
        self.skip_whitespace();
        let c = self.peek()?;

        match c {
            '$' => {
                self.pos += 1;
                Some(Param::Null)
            }
            '#' => {
                self.pos += 1;
                let id_str = self.read_while(|c| c.is_ascii_digit());
                u64::from_str(&id_str).ok().map(Param::Reference)
            }
            '\'' => {
                self.pos += 1;
                let mut s = String::new();
                while self.pos < self.input.len() {
                    let next = self.input[self.pos];
                    if next == '\'' {
                        // Check for escaped quote ''
                        if self.input.get(self.pos + 1) == Some(&'\'') {
                            s.push('\'');
                            self.pos += 2;
                            continue;
                        } else {
                            self.pos += 1;
                            break;
                        }
                    }
                    s.push(next);
                    self.pos += 1;
                }
                Some(Param::String(s))
            }
            '(' => self.parse_param_list().map(Param::List),
            '.' => {
                self.pos += 1;
                let e = self.read_while(|c| c.is_ascii_alphanumeric() || c == '_');
                if self.peek() == Some('.') {
                    self.pos += 1;
                }
                match e.as_str() {
                    "T" => Some(Param::Boolean(true)),
                    "F" => Some(Param::Boolean(false)),
                    "U" => Some(Param::Null), // Unknown as Null
                    _ => Some(Param::Enum(e)),
                }
            }
            _ if c.is_ascii_uppercase() => {
                // Typed parameter: CLASS_NAME(Value)
                let class = self.read_while(|c| c.is_ascii_alphanumeric() || c == '_');
                self.skip_whitespace();
                if self.peek() == Some('(') {
                    self.pos += 1;
                    let val = self.parse_single_param()?;
                    self.skip_whitespace();
                    if self.peek() == Some(')') {
                        self.pos += 1;
                    }
                    Some(Param::Typed(class, Box::new(val)))
                } else {
                    Some(Param::Enum(class)) // Fallback to enum if no parens
                }
            }
            _ if c.is_ascii_digit() || c == '-' || c == '.' => {
                let s = self.read_while(|c| {
                    c.is_ascii_digit() || c == '-' || c == '.' || c == 'e' || c == 'E' || c == '+'
                });
                
                if s.contains('.') || s.to_lowercase().contains('e') {
                    f64::from_str(&s).ok().map(Param::Float)
                } else {
                    i64::from_str(&s).ok().map(Param::Integer)
                }
            }
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lex_basic_entity() {
        let input = "#10= IFCSPACE('Main Office', $, .INTERNAL.);";
        let mut lexer = StepLexer::new(input);
        let entity = lexer.next_entity().unwrap();

        assert_eq!(entity.id, 10);
        assert_eq!(entity.class, "IFCSPACE");
        assert_eq!(entity.params.len(), 3);
        assert_eq!(entity.params[0], Param::String("Main Office".to_string()));
        assert_eq!(entity.params[1], Param::Null);
        assert_eq!(entity.params[2], Param::Enum("INTERNAL".to_string()));
    }

    #[test]
    fn test_lex_nested_list() {
        let input = "#20= IFCCARTESIANPOINT((1.0, 2.5, 3.0));";
        let mut lexer = StepLexer::new(input);
        let entity = lexer.next_entity().unwrap();

        assert_eq!(entity.class, "IFCCARTESIANPOINT");
        if let Param::List(inner) = &entity.params[0] {
            assert_eq!(inner.len(), 3);
            assert_eq!(inner[0], Param::Float(1.0));
            assert_eq!(inner[1], Param::Float(2.5));
            assert_eq!(inner[2], Param::Float(3.0));
        } else {
            panic!("Expected list parameter");
        }
    }

    #[test]
    fn test_lex_multiline() {
        let input = "
            #1= IFCPROJECT('guid', $, 'name');
            #2= IFCBUILDING('guid', #1);
        ";
        let mut lexer = StepLexer::new(input);
        let e1 = lexer.next_entity().unwrap();
        let e2 = lexer.next_entity().unwrap();

        assert_eq!(e1.id, 1);
        assert_eq!(e2.id, 2);
        assert_eq!(e2.params[1], Param::Reference(1));
    }
}
