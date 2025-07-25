# Direct Commands in Chat Assistant

The Chat Assistant now supports direct action commands ("Direct Commands") that bypass the AI model for faster and more precise control.

## Usage

Type commands starting with `#` in the chat input, for example:

```
#add flash to parcan_l at 5.2 duration 1.5
#add strobe to moving_head at 10 duration 2
#add flash to parcan_l at 5.2 for 1.5
#clear all actions confirm
#clear action 123
#clear group chorus
#render
#analyze
#analyze context
#create plan "Intro Flash" at 30s to 35s description "Opening sequence"
#list plans
#delete plan 1
#reset plans
#help
```

## Supported Commands

### Core Commands
- `#help` - Show a list of available commands
- `#tasks` - Show status of background tasks

### Action Management Commands
- `#clear all actions confirm` - Clear all actions from the current song (requires 'confirm' for safety)
- `#clear action <action_id>` - Clear a specific action by ID
- `#clear group <group_id>` - Clear all actions with a specific group ID
- `#add <action> to <fixture> at <start_time> duration <duration_time>` - Add a new action. Duration is optional, default is 1 beat.
- `#add <action> to <fixture> at <start_time> for <duration_time>` - Add a new action. Duration is optional, default is 1 beat.
- `#render` - Render all actions to the DMX canvas

### Light Plan Management Commands
- `#create plan <name> at <time> [to <end_time>] [description <description>]` - Create a new light plan item
- `#delete plan <id|name>` - Delete a light plan by ID or name
- `#reset plans` - Delete all light plans from the current song
- `#list plans` - Show all light plans in the current song

### Analysis Commands
- `#analyze` - Analyze the current song using the analysis service
- `#analyze context` - Generate lighting context for the current song using AI (runs in background, continues even if browser is closed, supports resume)
- `#analyze context reset` - Clear existing context analysis and start fresh (ignores previous progress)

## Accepted Time Formats

- `1m23.45s` (1 minute 23.45 seconds)
- `2b` (duration of 2 beats at the BPM of the current song)
- `12.5` (seconds)

## Light Plan Management

Light plans are metadata items that mark specific time ranges in a song for lighting design purposes. They help organize and plan lighting sequences.

### Creating Light Plans

```
#create plan <name> at <start_time> [to <end_time>] [description <description>]
```

**Examples:**
```
#create plan "Intro Flash" at 30s
#create plan "Drop Sequence" at 1m30s to 1m35s
#create plan "Verse Wash" at 45s to 1m15s description "Slow color wash during verse"
```

### Managing Light Plans

```
#list plans                    # Show all light plans
#delete plan <id>              # Delete by ID number
#delete plan "Intro Flash"     # Delete by name
#reset plans                   # Delete all light plans
```

**Examples:**
```
#list plans
#delete plan 1
#delete plan "Drop Sequence"
#reset plans
```

### Light Plan Features

- **Time Ranges**: Plans can have start time only, or start and end times
- **Descriptions**: Optional text descriptions for planning notes
- **Unique IDs**: Each plan gets a unique ID for easy reference
- **Name-based Access**: Delete plans by name or ID
- **Sorting**: Plans are displayed sorted by start time
- **Persistence**: Plans are saved with the song metadata

## Channel Value Normalization

- Channel values are interpreted as normalized values between `0.0` and `1.0`.
- `0.0` corresponds to the minimum DMX value (`0`).
- `1.0` corresponds to the maximum DMX value (`255`).
- Intermediate values are scaled linearly (e.g., `0.5` corresponds to `128`).

### Example:
```
#set parcan_l red channel to 0.5 at 12.23s
```
This sets the red channel of `parcan_l` to `128` at `12.23` seconds.

## Additional Direct Commands for DMX Canvas Painting

### Set Channel Value

- `#set <fixture> <channel_name> to <value> at <time>`
- Example:
  ```
  #set parcan_l red channel to 255 at 12.23s
  ```
- Purpose: Directly set a DMX channel value for a fixture at a specific time.

### Set Fixture Preset

- `#preset <fixture> <preset_name> at <time>`
- Example:
  ```
  #preset moving_head Drop at 34.2s
  ```
- Purpose: Apply a predefined fixture preset (e.g., "Drop") at a specific time.

### Fade Channel Value

- `#fade <fixture> <channel_name> from <start_value> to <end_value> duration <time>`
- Example:
  ```
  #fade parcan_l red channel from 0 to 255 duration 5s
  ```
- Purpose: Smoothly transition a channel value over a specified duration.

### Strobe Effect

- `#strobe <fixture> <channel_name> rate <frequency> duration <time>`
- Example:
  ```
  #strobe parcan_l white channel rate 10 duration 2s
  ```
- Purpose: Create a strobe effect by rapidly toggling a channel value.

### Clear Fixture State

- `#clear <fixture> state at <time>`
- Example:
  ```
  #clear parcan_l state at 15.0s
  ```
- Purpose: Reset a fixture's state at a specific time.

## Benefits of These Commands

- **Precision**: Users can directly control DMX channels and fixture states.
- **Flexibility**: Allows for custom effects beyond automated lighting plans.
- **Integration**: Complements automated pipelines by enabling manual overrides.
- **Planning**: Light plans help organize and structure lighting designs.
- **Metadata Management**: Light plans provide structured metadata for songs that can be used by AI systems and other tools.

## Notes

- All times are converted to seconds automatically
- You need to have a song loaded for these commands to work
- Light plan commands require a song to be loaded - you can't create, delete, or list light plans without a song
- After adding actions, use `#render` to see the results
- Direct commands appear in purple in the chat interface
- Background tasks (like `#analyze context`) continue running even if you close the browser
- Analysis supports automatic resume - if interrupted, it will continue from the last processed chunk
- Use `#analyze context reset` to clear previous progress and start completely fresh
- Partial results are saved every 5 chunks to prevent data loss
- Use `#tasks` to check the status of background operations
- Each background task gets a unique task ID for tracking
- Light plans are saved with the song metadata and persist between sessions
