# Keypad Manager - Product Requirements Document

## Overview

Keypad Manager is a Home Assistant custom integration that provides a centralized system for managing keypad codes, RFID tags, and their associated access permissions. The integration acts as a validation service that can be called by Home Assistant automations to determine whether a provided code or tag should trigger an automation.

## Core Functionality

### Primary Use Case
1. **Code/Tag Validation**: Receive a code or tag input from an automation
2. **Permission Checking**: Validate if the code/tag exists and is authorized
3. **Schedule Validation**: Check if the code/tag is valid for the current time
4. **Automation Control**: Return success/failure to control automation flow
5. **Logging**: Record all access attempts (successful and failed)

### Data Model

#### Users Table
- **Name** (string): Human-readable name for the user
- **Code** (string, optional): Numeric keypad code, 4-8 digits (must be unique if provided)
- **Tag** (string, optional): RFID tag identifier (must be unique if provided)
- **Active** (boolean): Whether this user is currently active
- **Created** (datetime): When the user was created
- **Last Used** (datetime): Last successful access

**Uniqueness Constraints:**
- Each code must be unique across all users (no two users can have the same code)
- Each tag must be unique across all users (no two users can have the same tag)
- A user can have both a code and a tag, but each must be unique
- Empty/null codes and tags are allowed (for users with only one type of access)

#### Schedules Table
- **User ID** (foreign key): Reference to user
- **Day of Week** (integer): 0-6 (Monday-Sunday)
- **Start Time** (time): When access is allowed to begin
- **End Time** (time): When access expires
- **Active** (boolean): Whether this schedule is active

#### Access Events
The integration uses Home Assistant's native event system for logging all access attempts:

**Event: `keypad_manager_code_validated`**
- **user_id** (string): ID of the user
- **user_name** (string): Name of the user
- **code** (string): The code that was entered
- **source** (string): Identifier for the calling automation
- **timestamp** (datetime): When the validation occurred

**Event: `keypad_manager_tag_validated`**
- **user_id** (string): ID of the user
- **user_name** (string): Name of the user
- **tag** (string): The tag that was entered
- **source** (string): Identifier for the calling automation
- **timestamp** (datetime): When the validation occurred

**Event: `keypad_manager_code_failed`**
- **code** (string): The code that was entered
- **source** (string): Identifier for the calling automation
- **reason** (string): "INVALID_CODE", "INVALID_SCHEDULE", "INACTIVE_USER"
- **timestamp** (datetime): When the validation occurred

**Event: `keypad_manager_tag_failed`**
- **tag** (string): The tag that was entered
- **source** (string): Identifier for the calling automation
- **reason** (string): "INVALID_TAG", "INVALID_SCHEDULE", "INACTIVE_USER"
- **timestamp** (datetime): When the validation occurred

## Integration Architecture

### Domain
- **Domain Name**: `keypad_manager`
- **Integration Name**: "Keypad Manager"

### Services

#### `keypad_manager.validate_code`
**Purpose**: Validate a keypad code
**Parameters**:
- `code` (string, required): The keypad code to validate
- `source` (string, optional): Identifier for the calling automation

**Returns**:
- `valid` (boolean): Whether the code is valid and authorized
- `user_name` (string, optional): Name of the user if valid
- `reason` (string): Reason for failure if invalid

#### `keypad_manager.validate_tag`
**Purpose**: Validate an RFID tag
**Parameters**:
- `tag` (string, required): The RFID tag to validate
- `source` (string, optional): Identifier for the calling automation

**Returns**:
- `valid` (boolean): Whether the tag is valid and authorized
- `user_name` (string, optional): Name of the user if valid
- `reason` (string): Reason for failure if invalid

#### `keypad_manager.add_user`
**Purpose**: Add a new user with codes/tags
**Parameters**:
- `name` (string, required): User's name
- `code` (string, optional): Keypad code (must be unique if provided)
- `tag` (string, optional): RFID tag (must be unique if provided)
- `schedules` (list, optional): List of schedule dictionaries

**Validation Rules**:
- `name` cannot be empty
- `code` must be unique across all users (if provided)
- `tag` must be unique across all users (if provided)
- At least one of `code` or `tag` must be provided
- Returns error if uniqueness constraints are violated

#### `keypad_manager.remove_user`
**Purpose**: Remove a user
**Parameters**:
- `user_id` (string, required): ID of user to remove

### Entities

#### Binary Sensor: `keypad_manager.last_access`
- **State**: `on` if last access was successful, `off` if failed
- **Attributes**:
  - `user_name`: Name of user who last accessed
  - `timestamp`: When the last access occurred
  - `source`: Source of the access attempt
  - `reason`: Reason for success/failure

#### Sensor: `keypad_manager.active_users`
- **State**: Number of currently active users
- **Attributes**:
  - `total_users`: Total number of users
  - `users_with_codes`: Number of users with keypad codes
  - `users_with_tags`: Number of users with RFID tags

#### Sensor: `keypad_manager.access_count_today`
- **State**: Number of access attempts today
- **Attributes**:
  - `successful_accesses`: Number of successful accesses today
  - `failed_accesses`: Number of failed accesses today

## Configuration

### Config Flow
1. **Initial Setup**: No configuration required initially
2. **User Management**: Web UI for adding/removing users
3. **Schedule Management**: Web UI for setting access schedules
4. **Logging Configuration**: Optional settings for log retention

### Configuration Options
- **Default Access Time** (time): Default time range if no schedule specified
- **Enable Debug Logging** (boolean): Enable detailed logging

## User Interface

### Configuration Panel
- **Users Tab**: Add, edit, remove users and their codes/tags
- **Schedules Tab**: Manage access schedules for each user
- **Events Tab**: View recent access events (via HA's event system)
- **Settings Tab**: Configure default options

### User Management Features
- Add new users with name, code, and/or tag
- Edit existing users
- Deactivate users (soft delete)
- Bulk import/export users
- Search and filter users

### Schedule Management Features
- Set daily schedules for each user
- Multiple time ranges per day
- Copy schedules between users
- Quick templates (weekdays, weekends, etc.)

## Automation Integration

### Example Automation Usage

#### Keypad Code Validation
```yaml
automation:
  - alias: "Keypad Door Unlock"
    trigger:
      - platform: state
        entity_id: sensor.keypad_input
    action:
      - service: keypad_manager.validate_code
        data:
          code: "{{ states('sensor.keypad_input') }}"
          source: "front_door"
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ result.valid }}"
            sequence:
              - service: lock.unlock
                target:
                  entity_id: lock.front_door
              - service: notify.mobile_app
                data:
                  message: "Door unlocked by {{ result.user_name }}"
```

### Event-Based Automation Examples

#### Monitor Successful Access
```yaml
automation:
  - alias: "Monitor Successful Access"
    trigger:
      - platform: event
        event_type: keypad_manager_code_validated
      - platform: event
        event_type: keypad_manager_tag_validated
    action:
      - service: persistent_notification.create
        data:
          title: "✅ Successful Access"
          message: |
            User: {{ trigger.event.data.user_name }}
            Source: {{ trigger.event.data.source }}
            Time: {{ trigger.event.data.timestamp }}
```

#### Monitor Failed Access Attempts
```yaml
automation:
  - alias: "Monitor Failed Access"
    trigger:
      - platform: event
        event_type: keypad_manager_code_failed
      - platform: event
        event_type: keypad_manager_tag_failed
    action:
      - service: persistent_notification.create
        data:
          title: "❌ Failed Access Attempt"
          message: |
            Source: {{ trigger.event.data.source }}
            Code/Tag: {{ trigger.event.data.code or trigger.event.data.tag }}
            Reason: {{ trigger.event.data.reason }}
            Time: {{ trigger.event.data.timestamp }}
```

#### Security Alert for Failed Attempts
```yaml
automation:
  - alias: "Security Alert - Failed Access"
    trigger:
      - platform: event
        event_type: keypad_manager_code_failed
      - platform: event
        event_type: keypad_manager_tag_failed
    action:
      - service: notify.mobile_app
        data:
          title: "🚨 Security Alert"
          message: |
            Failed access attempt detected!
            Location: {{ trigger.event.data.source }}
            Input: {{ trigger.event.data.code or trigger.event.data.tag }}
            Reason: {{ trigger.event.data.reason }}
```

#### RFID Tag Validation
```yaml
automation:
  - alias: "RFID Door Unlock"
    trigger:
      - platform: state
        entity_id: sensor.rfid_reader
    action:
      - service: keypad_manager.validate_tag
        data:
          tag: "{{ states('sensor.rfid_reader') }}"
          source: "front_door"
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ result.valid }}"
            sequence:
              - service: lock.unlock
                target:
                  entity_id: lock.front_door
              - service: notify.mobile_app
                data:
                  message: "Door unlocked by {{ result.user_name }}"
```

## Data Storage

### Storage Method
- **Home Assistant Storage**: Use HA's built-in storage system
- **JSON Files**: Store data in `keypad_manager.json` in HA config
- **Backup/Restore**: Include in HA backups automatically
- **Events**: Access logs handled by HA's native event system

### Data Structure
```json
{
  "users": [
    {
      "id": "user_123",
      "name": "John Doe",
      "code": "1234",
      "tag": "ABC123",
      "active": true,
      "created": "2024-01-01T00:00:00Z",
      "last_used": "2024-01-15T10:30:00Z"
    }
  ],
  "schedules": [
    {
      "user_id": "user_123",
      "day_of_week": 1,
      "start_time": "08:00:00",
      "end_time": "18:00:00",
      "active": true
    }
  ],
  "settings": {
    "default_access_time": "00:00:00-23:59:59",
    "debug_logging": false
  }
}
```

## Data Validation and Error Handling

### Uniqueness Enforcement
- **Code Uniqueness**: Each keypad code must be unique across all users
- **Tag Uniqueness**: Each RFID tag must be unique across all users
- **Validation on Add**: Check uniqueness when adding new users
- **Validation on Edit**: Check uniqueness when updating existing users
- **Error Messages**: Clear error messages when uniqueness is violated

### Input Validation
- **Code Format**: Validate code format (4-8 digits only)
- **Tag Format**: Validate tag format (0-9999, numeric only)
- **Name Validation**: Ensure user names are not empty
- **Schedule Validation**: Validate time ranges and day formats

### Error Handling
- **Duplicate Code**: "Code '1234' is already assigned to user 'John Doe'"
- **Duplicate Tag**: "Tag 'ABC123' is already assigned to user 'Jane Smith'"
- **Invalid Format**: "Code must be 4-8 digits"
- **Missing Required**: "User must have either a code or tag"

## Security Considerations

### Access Control
- Only Home Assistant administrators can manage users
- No external API access
- All data stored locally within Home Assistant
- No network connectivity required

### Data Protection
- **Encrypted Codes**: Keypad codes are encrypted using PBKDF2 with SHA256
- **Plain Text Tags**: RFID tags stored in plain text (validated by hardware)
- **Unique Salts**: Each code uses a unique 32-byte salt for maximum security
- **Secure Comparison**: Uses constant-time comparison to prevent timing attacks
- **Hardware Validation**: RFID tags rely on hardware-level security
- **Access Events**: Handled by Home Assistant's native event system
- **User Management**: Restricted to Home Assistant administrators

### Encryption Details
- **Algorithm**: PBKDF2 with SHA256 (for codes only)
- **Iterations**: 100,000 rounds for strong security
- **Salt Length**: 32 bytes (64 hex characters)
- **Storage**: Encrypted codes and plain text tags in Home Assistant storage

## Implementation Phases

### Phase 1: Core Functionality
- [ ] Basic integration structure
- [ ] User management (add/remove users)
- [ ] Code/tag validation service
- [ ] Event system integration
- [ ] Configuration UI

### Phase 2: Scheduling
- [ ] Schedule management
- [ ] Time-based validation
- [ ] Schedule UI components

### Phase 3: Advanced Features
- [ ] Enhanced event analytics and reporting
- [ ] Bulk import/export
- [ ] Advanced automation helpers
- [ ] Statistics and analytics

### Phase 4: Polish
- [ ] Error handling improvements
- [ ] Performance optimizations
- [ ] Documentation
- [ ] Testing

## Success Metrics

### Functional Requirements
- [ ] Can validate codes and tags successfully
- [ ] Can enforce time-based access restrictions
- [ ] Can emit events for all access attempts
- [ ] Can integrate with Home Assistant automations
- [ ] Provides user-friendly management interface

### Performance Requirements
- [ ] Validation response time < 100ms
- [ ] Support for 100+ users without performance degradation
- [ ] Event emission overhead < 50ms
- [ ] Memory usage < 10MB for typical installations

## Future Enhancements

### Potential Features
- **Geofencing**: Allow access based on user location
- **Temporary Codes**: Time-limited access codes
- **Integration APIs**: Connect to external access control systems
- **Mobile App**: Companion app for code management
- **Advanced Analytics**: Usage patterns and security insights
- **Multi-site Support**: Manage multiple locations
- **Webhook Support**: Real-time notifications to external systems

---

*This PRD serves as the foundation for developing the Keypad Manager integration. It will be updated as requirements evolve during development.*