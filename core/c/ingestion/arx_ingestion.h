/**
 * @file arx_ingestion.h
 * @brief ARXOS Ingestion System - High-performance file parsing and object creation
 * 
 * Provides ultra-fast parsing of building plan files (PDF, IFC, DWG, images)
 * and converts them directly to ArxObjects for immediate use in the ASCII-BIM system.
 */

#ifndef ARX_INGESTION_H
#define ARX_INGESTION_H

#ifdef __cplusplus
extern "C" {
#endif

#include "arxobject/arxobject.h"
#include <stdbool.h>
#include <stdint.h>

// ============================================================================
// INGESTION TYPES AND STRUCTURES
// ============================================================================

/**
 * @brief Supported file formats for ingestion
 */
typedef enum {
    ARX_FORMAT_PDF = 0,
    ARX_FORMAT_IFC = 1,
    ARX_FORMAT_DWG = 2,
    ARX_FORMAT_IMAGE = 3,
    ARX_FORMAT_EXCEL = 4,
    ARX_FORMAT_LIDAR = 5,
    ARX_FORMAT_UNKNOWN = 99
} ArxFileFormat;

/**
 * @brief Ingestion processing options
 */
typedef struct {
    bool enable_merging;
    float min_confidence;
    bool require_validation;
    char coordinate_system[64];
    char units_of_measure[32];
    int max_objects_per_file;
    bool enable_caching;
} ArxIngestionOptions;

/**
 * @brief Ingestion processing result
 */
typedef struct {
    bool success;
    char* error_message;
    ArxObject** objects;
    int object_count;
    float overall_confidence;
    double processing_time_ms;
    char* file_info;
    char* validation_summary;
} ArxIngestionResult;

/**
 * @brief File metadata extracted during ingestion
 */
typedef struct {
    char filename[256];
    ArxFileFormat format;
    uint64_t file_size;
    int page_count;
    char building_name[128];
    char building_type[64];
    int year_built;
    float total_area;
    int num_floors;
} ArxFileMetadata;

// ============================================================================
// CORE INGESTION FUNCTIONS
// ============================================================================

/**
 * @brief Initialize the ingestion system
 * @return true on success, false on failure
 */
bool arx_ingestion_init(void);

/**
 * @brief Cleanup the ingestion system
 */
void arx_ingestion_cleanup(void);

/**
 * @brief Detect file format from file path
 * @param filepath Path to the file
 * @return Detected file format
 */
ArxFileFormat arx_ingestion_detect_format(const char* filepath);

/**
 * @brief Get file metadata without full parsing
 * @param filepath Path to the file
 * @param metadata Output metadata structure
 * @return true on success, false on failure
 */
bool arx_ingestion_get_metadata(const char* filepath, ArxFileMetadata* metadata);

/**
 * @brief Process a file and create ArxObjects
 * @param filepath Path to the file
 * @param options Processing options
 * @return Processing result with created objects
 */
ArxIngestionResult* arx_ingestion_process_file(const char* filepath, const ArxIngestionOptions* options);

/**
 * @brief Free ingestion result and all associated memory
 * @param result Result to free
 */
void arx_ingestion_free_result(ArxIngestionResult* result);

// ============================================================================
// FORMAT-SPECIFIC PROCESSORS
// ============================================================================

/**
 * @brief Process PDF building plans
 * @param filepath Path to PDF file
 * @param options Processing options
 * @return Processing result
 */
ArxIngestionResult* arx_ingestion_process_pdf(const char* filepath, const ArxIngestionOptions* options);

/**
 * @brief Process IFC BIM models
 * @param filepath Path to IFC file
 * @param options Processing options
 * @return Processing result
 */
ArxIngestionResult* arx_ingestion_process_ifc(const char* filepath, const ArxIngestionOptions* options);

/**
 * @brief Process DWG/DXF CAD files
 * @param filepath Path to DWG/DXF file
 * @param options Processing options
 * @return Processing result
 */
ArxIngestionResult* arx_ingestion_process_dwg(const char* filepath, const ArxIngestionOptions* options);

/**
 * @brief Process image files (HEIC, JPEG, PNG)
 * @param filepath Path to image file
 * @param options Processing options
 * @return Processing result
 */
ArxIngestionResult* arx_ingestion_process_image(const char* filepath, const ArxIngestionOptions* options);

/**
 * @brief Process Excel/CSV files
 * @param filepath Path to Excel/CSV file
 * @param options Processing options
 * @return Processing result
 */
ArxIngestionResult* arx_ingestion_process_excel(const char* filepath, const ArxIngestionOptions* options);

/**
 * @brief Process LiDAR point clouds
 * @param filepath Path to LiDAR file
 * @param options Processing options
 * @return Processing result
 */
ArxIngestionResult* arx_ingestion_process_lidar(const char* filepath, const ArxIngestionOptions* options);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * @brief Get default ingestion options
 * @return Default options structure
 */
ArxIngestionOptions arx_ingestion_get_default_options(void);

/**
 * @brief Validate ingestion options
 * @param options Options to validate
 * @return true if valid, false if invalid
 */
bool arx_ingestion_validate_options(const ArxIngestionOptions* options);

/**
 * @brief Get supported file formats as string array
 * @param formats Output array of format strings
 * @param max_formats Maximum number of formats to return
 * @return Number of formats returned
 */
int arx_ingestion_get_supported_formats(char** formats, int max_formats);

/**
 * @brief Get processing statistics
 * @return Statistics string (caller must free)
 */
char* arx_ingestion_get_statistics(void);

/**
 * @brief Clear processing statistics
 */
void arx_ingestion_clear_statistics(void);

#ifdef __cplusplus
}
#endif

#endif // ARX_INGESTION_H
