# Terminal Navigation System

## Moving Through Buildings Like a Game

### Navigation Modes

#### WASD Movement
```bash
W - Move North
A - Move West  
S - Move South
D - Move East
Q - Up floor
E - Down floor
```

#### Path-Based
```bash
$ arxos goto @room-201
$ arxos goto @outlet-4A7B
$ arxos goto coordinates:1000,2000,1500
```

#### Search Navigation
```bash
$ arxos find "conference room"
$ arxos find type:outlet status:fault
$ arxos find player:Mike
```

### Filesystem Metaphor

```bash
# Buildings as directories
$ arxos cd /campus/building-a/floor-2/room-201
$ arxos ls
outlets/
  outlet-01 [ON, 15A]
  outlet-02 [OFF]
sensors/
  temp-01 [72°F]
  motion-01 [CLEAR]

$ arxos pwd
/campus/building-a/floor-2/room-201
```

### Quick Actions

```bash
TAB     - Cycle through nearby objects
SPACE   - Interact with object
ENTER   - Enter detail view
ESC     - Exit to higher level
/       - Start search
m       - Toggle map
p       - Show players
h       - Help
```

### Bookmarks

```bash
# Save locations
$ arxos bookmark add "electrical-room"
$ arxos bookmark add "my-office"

# Jump to bookmarks
$ arxos bookmark goto electrical-room
```

---

→ Next: [Implementation](../06-implementation/)