/*!
 * @file arxos_mobile.h
 * @brief C FFI bindings for ArxOS mobile integration
 * 
 * This header provides C-compatible function exports for iOS and Android.
 * Functions return JSON strings that must be freed by the caller using arxos_free_string().
 */

#ifndef ARXOS_MOBILE_H
#define ARXOS_MOBILE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/*!
 * @brief Free a string allocated by ArxOS
 * 
 * @param ptr Pointer to the string to free
 * @note Must only be called with pointers returned from ArxOS FFI functions
 */
void arxos_free_string(char* ptr);

/*!
 * @brief Get the last error code from the last operation
 * 
 * @return Error code (0 = Success, 1 = NotFound, 2 = InvalidData, 3 = IoError)
 */
int32_t arxos_last_error(void);

/*!
 * @brief Get the last error message
 * 
 * @return Pointer to error message string (must be freed with arxos_free_string)
 */
char* arxos_last_error_message(void);

/*!
 * @brief List all rooms in a building
 * 
 * @param building_name Name of the building (UTF-8 null-terminated string)
 * @return JSON string containing array of RoomInfo objects (must be freed with arxos_free_string)
 */
char* arxos_list_rooms(const char* building_name);

/*!
 * @brief Get a specific room by ID
 * 
 * @param building_name Name of the building
 * @param room_id ID or name of the room
 * @return JSON string containing RoomInfo object (must be freed with arxos_free_string)
 */
char* arxos_get_room(const char* building_name, const char* room_id);

/*!
 * @brief List all equipment in a building
 * 
 * @param building_name Name of the building
 * @return JSON string containing array of EquipmentInfo objects (must be freed with arxos_free_string)
 */
char* arxos_list_equipment(const char* building_name);

/*!
 * @brief Get a specific equipment item by ID
 * 
 * @param building_name Name of the building
 * @param equipment_id ID or name of the equipment
 * @return JSON string containing EquipmentInfo object (must be freed with arxos_free_string)
 */
char* arxos_get_equipment(const char* building_name, const char* equipment_id);

/*!
 * @brief Parse AR scan data from JSON string
 * 
 * @param json_data JSON string containing AR scan data
 * @return JSON string containing parsed ARScanData (must be freed with arxos_free_string)
 */
char* arxos_parse_ar_scan(const char* json_data);

/*!
 * @brief Process AR scan and extract equipment information
 * 
 * @param json_data JSON string containing AR scan data
 * @return JSON string containing array of EquipmentInfo objects (must be freed with arxos_free_string)
 */
char* arxos_extract_equipment(const char* json_data);

/*!
 * @brief Process AR scan and create pending equipment items
 * 
 * @param json_data JSON string containing AR scan data from mobile
 * @param building_name Name of building for context
 * @param confidence_threshold Minimum confidence (0.0-1.0) to create pending items
 * @return JSON string with pending equipment IDs and details (must be freed with arxos_free_string)
 */
char* arxos_process_ar_scan_to_pending(const char* json_data, const char* building_name, double confidence_threshold);

/*!
 * @brief Export building to AR-compatible format
 * 
 * @param building_name Name of building to export
 * @param format Export format: "gltf" or "usdz"
 * @return JSON string with export status and file path (must be freed with arxos_free_string)
 */
char* arxos_export_for_ar(const char* building_name, const char* format);

#ifdef __cplusplus
}
#endif

#endif // ARXOS_MOBILE_H

