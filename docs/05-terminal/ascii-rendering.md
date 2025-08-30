# ASCII Rendering Engine

## Building Visualization in Pure Text

### Rendering Pipeline

```rust
ArxObjects → Spatial Index → View Frustum → ASCII Buffer → Terminal
```

### Drawing Algorithm

```rust
fn render_floor(floor: &Floor) -> String {
    let mut buffer = AsciiBuffer::new(80, 24);
    
    // Draw walls
    for wall in floor.walls {
        buffer.draw_line(wall.start, wall.end, '═');
    }
    
    // Draw rooms
    for room in floor.rooms {
        buffer.draw_rect(room.bounds, '│', '─');
        buffer.put_text(room.center, &room.number);
    }
    
    // Draw objects
    for obj in floor.objects {
        let symbol = match obj.object_type {
            TYPE_OUTLET => '○',
            TYPE_LIGHT => '☼',
            TYPE_SENSOR => '◊',
            _ => '?'
        };
        buffer.put_char(obj.position, symbol);
    }
    
    buffer.to_string()
}
```

### Optimization Techniques

- **Dirty rectangles**: Only redraw changed areas
- **Double buffering**: Smooth updates
- **Spatial indexing**: Fast object lookup
- **Level-of-detail**: Simplify distant objects

### Special Effects

```
Blinking:   ● ○ ● ○  (Alerts)
Animation:  ⣾⣽⣻⢿⡿⣟⣯⣷  (Loading)
Intensity:  ░ ▒ ▓ █  (Heat maps)
```

---

→ Next: [Zoom Levels](zoom-levels.md)