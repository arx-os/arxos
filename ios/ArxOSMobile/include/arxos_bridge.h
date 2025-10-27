//
//  arxos_bridge.h
//  ArxOSMobile
//
//  Bridge header for ArxOS C FFI integration
//

#ifndef arxos_bridge_h
#define arxos_bridge_h

#import <Foundation/Foundation.h>

// Import the FFI functions
// Note: In production, these would be linked from the compiled .a or .framework
// For now, we declare them as forward declarations

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations of ArxOS FFI functions
void arxos_free_string(char* ptr);
int32_t arxos_last_error(void);
char* arxos_last_error_message(void);
char* arxos_list_rooms(const char* building_name);
char* arxos_get_room(const char* building_name, const char* room_id);
char* arxos_list_equipment(const char* building_name);
char* arxos_get_equipment(const char* building_name, const char* equipment_id);
char* arxos_parse_ar_scan(const char* json_data);
char* arxos_extract_equipment(const char* json_data);

#ifdef __cplusplus
}
#endif

#endif /* arxos_bridge_h */

