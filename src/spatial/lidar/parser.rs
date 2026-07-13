use crate::core::spatial::Point3D;
use anyhow::{anyhow, Result};
use las::Read;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

/// Stream points from a point cloud file (CSV, XYZ, PLY, or LAS)
pub fn stream_points(path: &Path) -> Result<Box<dyn Iterator<Item = Result<Point3D>>>> {
    // 1. Try to detect by reading the first few bytes
    if let Ok(mut file) = File::open(path) {
        use std::io::Read;
        let mut magic = [0u8; 4];
        if file.read_exact(&mut magic).is_ok() {
            if &magic == b"LASF" {
                return Ok(Box::new(stream_las(path)?));
            }
            if &magic[..3] == b"ply" {
                return Ok(Box::new(stream_ply(path)?));
            }
        }
    }

    // 2. Fallback to extension check
    let extension = path
        .extension()
        .and_then(|ext| ext.to_str())
        .map(|s| s.to_lowercase());

    match extension.as_deref() {
        Some("csv") | Some("xyz") | Some("txt") => Ok(Box::new(stream_xyz_csv(path)?)),
        Some("ply") => Ok(Box::new(stream_ply(path)?)),
        Some("las") | Some("laz") => Ok(Box::new(stream_las(path)?)),
        _ => {
            // Default fallback to text-based parsing
            Ok(Box::new(stream_xyz_csv(path)?))
        }
    }
}

struct XyzIterator {
    reader: BufReader<File>,
}

impl Iterator for XyzIterator {
    type Item = Result<Point3D>;

    fn next(&mut self) -> Option<Self::Item> {
        let mut line = String::new();
        loop {
            line.clear();
            match self.reader.read_line(&mut line) {
                Ok(0) => return None, // EOF
                Ok(_) => {
                    let trimmed = line.trim();
                    if trimmed.is_empty() || trimmed.starts_with('#') {
                        continue;
                    }
                    let parts: Vec<&str> = trimmed
                        .split([',', ' ', '\t', ';'])
                        .filter(|s| !s.is_empty())
                        .collect();

                    if parts.len() < 3 {
                        return Some(Err(anyhow!("Invalid point line format: '{}'", trimmed)));
                    }

                    let x = match parts[0].parse::<f64>() {
                        Ok(val) => val,
                        Err(_) => return Some(Err(anyhow!("Failed to parse x: '{}'", parts[0]))),
                    };
                    let y = match parts[1].parse::<f64>() {
                        Ok(val) => val,
                        Err(_) => return Some(Err(anyhow!("Failed to parse y: '{}'", parts[1]))),
                    };
                    let z = match parts[2].parse::<f64>() {
                        Ok(val) => val,
                        Err(_) => return Some(Err(anyhow!("Failed to parse z: '{}'", parts[2]))),
                    };

                    return Some(Ok(Point3D::new(x, y, z)));
                }
                Err(e) => return Some(Err(anyhow!("Failed to read line: {}", e))),
            }
        }
    }
}

/// Simple space/comma-separated value parser (streaming)
fn stream_xyz_csv(path: &Path) -> Result<impl Iterator<Item = Result<Point3D>>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    Ok(XyzIterator { reader })
}

struct PlyIterator {
    reader: BufReader<File>,
}

impl Iterator for PlyIterator {
    type Item = Result<Point3D>;

    fn next(&mut self) -> Option<Self::Item> {
        let mut line = String::new();
        loop {
            line.clear();
            match self.reader.read_line(&mut line) {
                Ok(0) => return None,
                Ok(_) => {
                    let trimmed = line.trim();
                    if trimmed.is_empty() {
                        continue;
                    }
                    let parts: Vec<&str> = trimmed.split_whitespace().collect();
                    if parts.len() < 3 {
                        return Some(Err(anyhow!("Invalid PLY vertex format: '{}'", trimmed)));
                    }

                    let x = match parts[0].parse::<f64>() {
                        Ok(val) => val,
                        Err(_) => {
                            return Some(Err(anyhow!("Failed to parse PLY x: '{}'", parts[0])))
                        }
                    };
                    let y = match parts[1].parse::<f64>() {
                        Ok(val) => val,
                        Err(_) => {
                            return Some(Err(anyhow!("Failed to parse PLY y: '{}'", parts[1])))
                        }
                    };
                    let z = match parts[2].parse::<f64>() {
                        Ok(val) => val,
                        Err(_) => {
                            return Some(Err(anyhow!("Failed to parse PLY z: '{}'", parts[2])))
                        }
                    };

                    return Some(Ok(Point3D::new(x, y, z)));
                }
                Err(e) => return Some(Err(anyhow!("Failed to read line: {}", e))),
            }
        }
    }
}

/// Lightweight ASCII PLY parser (streaming after header)
fn stream_ply(path: &Path) -> Result<impl Iterator<Item = Result<Point3D>>> {
    let file = File::open(path)?;
    let mut reader = BufReader::new(file);

    // 1. Parse header
    let mut header_ended = false;
    let mut line = String::new();

    while !header_ended {
        line.clear();
        let bytes_read = reader.read_line(&mut line)?;
        if bytes_read == 0 {
            return Err(anyhow!("Reached EOF before PLY header ended"));
        }

        let trimmed = line.trim();
        if trimmed == "end_header" {
            header_ended = true;
        }
    }

    Ok(PlyIterator { reader })
}

struct LasIterator<'a> {
    reader: las::Reader<'a>,
}

impl<'a> Iterator for LasIterator<'a> {
    type Item = Result<Point3D>;

    fn next(&mut self) -> Option<Self::Item> {
        match self.reader.read() {
            Some(Ok(p)) => Some(Ok(Point3D::new(p.x, p.y, p.z))),
            None => None,
            Some(Err(e)) => Some(Err(anyhow!("LAS reader error: {}", e))),
        }
    }
}

/// Streaming reader for LAS binary point clouds using `las` crate
fn stream_las(path: &Path) -> Result<impl Iterator<Item = Result<Point3D>> + 'static> {
    let reader = las::Reader::from_path(path)?;
    Ok(LasIterator { reader })
}
