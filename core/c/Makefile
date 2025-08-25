# ARXOS C Core Makefile
# Builds the complete C foundation for ARXOS

# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -g -fPIC
LDFLAGS = -lpthread -lm

# Directories
SRC_DIR = .
INCLUDE_DIR = ../include
LIB_DIR = ../lib
BIN_DIR = ../bin
TEST_DIR = test

# Source files for each component
ARXOBJECT_SOURCES = arxobject/arxobject.c
ASCII_SOURCES = ascii/ascii_engine.c
BUILDING_SOURCES = building/arx_building.c
VERSION_SOURCES = version/arx_version.c
SPATIAL_SOURCES = spatial/arx_spatial.c
INGESTION_SOURCES = ingestion/arx_ingestion.c
AUTH_SOURCES = auth/arx_auth.c
DATABASE_SOURCES = database/arx_database.c
WALL_COMPOSITION_SOURCES = wall_composition/arx_wall_composition.c
CGO_SOURCES = cgo/bridge.c

# Combined sources
SOURCES = $(ARXOBJECT_SOURCES) $(ASCII_SOURCES) $(BUILDING_SOURCES) $(VERSION_SOURCES) $(SPATIAL_SOURCES) $(INGESTION_SOURCES) $(AUTH_SOURCES) $(DATABASE_SOURCES) $(WALL_COMPOSITION_SOURCES) $(CGO_SOURCES)

# Object files
OBJECTS = $(SOURCES:.c=.o)

# Libraries
ARXOBJECT_LIBRARY = libarxobject.a
ASCII_LIBRARY = libascii.a
BUILDING_LIBRARY = libarxbuilding.a
VERSION_LIBRARY = libarxversion.a
SPATIAL_LIBRARY = libarxspatial.a
INGESTION_LIBRARY = libarxingestion.a
AUTH_LIBRARY = libarxauth.a
DATABASE_LIBRARY = libarxdatabase.a
WALL_COMPOSITION_LIBRARY = libarxwallcomposition.a
CGO_LIBRARY = libarxoscgo.a
SHARED_LIB = libarxos.so

# Main targets
all: $(LIB_DIR)/$(ARXOBJECT_LIBRARY) $(LIB_DIR)/$(ASCII_LIBRARY) \
     $(LIB_DIR)/$(BUILDING_LIBRARY) $(LIB_DIR)/$(VERSION_LIBRARY) \
     $(LIB_DIR)/$(SPATIAL_LIBRARY) $(LIB_DIR)/$(INGESTION_LIBRARY) $(LIB_DIR)/$(AUTH_LIBRARY) $(LIB_DIR)/$(DATABASE_LIBRARY) $(LIB_DIR)/$(WALL_COMPOSITION_LIBRARY) $(LIB_DIR)/$(CGO_LIBRARY) $(LIB_DIR)/$(SHARED_LIB)

# Create library directories
$(LIB_DIR):
	mkdir -p $(LIB_DIR)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# ArxObject Runtime Engine
$(LIB_DIR)/$(ARXOBJECT_LIBRARY): $(LIB_DIR) arxobject/arxobject.o
	ar rcs $@ arxobject/arxobject.o

# ASCII-BIM Spatial Engine
$(LIB_DIR)/$(ASCII_LIBRARY): $(LIB_DIR) ascii/ascii_engine.o
	ar rcs $@ ascii/ascii_engine.o

# Building Management System
$(LIB_DIR)/$(BUILDING_LIBRARY): $(LIB_DIR) building/arx_building.o
	ar rcs $@ building/arx_building.o

# Version Control System
$(LIB_DIR)/$(VERSION_LIBRARY): $(LIB_DIR) version/arx_version.o
	ar rcs $@ version/arx_version.o

# Spatial Indexing System
$(LIB_DIR)/$(SPATIAL_LIBRARY): $(LIB_DIR) spatial/arx_spatial.o
	ar rcs $@ spatial/arx_spatial.o

# Ingestion System
$(LIB_DIR)/$(INGESTION_LIBRARY): $(LIB_DIR) ingestion/arx_ingestion.o
	ar rcs $@ ingestion/arx_ingestion.o

# Authentication System
$(LIB_DIR)/$(AUTH_LIBRARY): $(LIB_DIR) auth/arx_auth.o
	ar rcs $@ auth/arx_auth.o

# Database System
$(LIB_DIR)/$(DATABASE_LIBRARY): $(LIB_DIR) database/arx_database.o
	ar rcs $@ database/arx_database.o

# Wall Composition System
$(LIB_DIR)/$(WALL_COMPOSITION_LIBRARY): $(LIB_DIR) wall_composition/arx_wall_composition.o
	ar rcs $@ wall_composition/arx_wall_composition.o

# CGO Bridge
$(LIB_DIR)/$(CGO_LIBRARY): $(LIB_DIR) cgo/bridge.o
	ar rcs $@ cgo/bridge.o

# Combined shared library
$(LIB_DIR)/$(SHARED_LIB): $(LIB_DIR) $(OBJECTS)
	$(CC) -shared -o $@ $(OBJECTS) $(LDFLAGS)

# Object file compilation
arxobject/arxobject.o: arxobject/arxobject.c arxobject/arxobject.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

wall_composition/arx_wall_composition.o: wall_composition/arx_wall_composition.c wall_composition/arx_wall_composition.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

ascii/ascii_engine.o: ascii/ascii_engine.c ascii/ascii_engine.h arxobject/arxobject.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

building/arx_building.o: building/arx_building.c building/arx_building.h arxobject/arxobject.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

version/arx_version.o: version/arx_version.c version/arx_version.h arxobject/arxobject.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

spatial/arx_spatial.o: spatial/arx_spatial.c spatial/arx_spatial.h arxobject/arxobject.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

ingestion/arx_ingestion.o: ingestion/arx_ingestion.c ingestion/arx_ingestion.h arxobject/arxobject.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

auth/arx_auth.o: auth/arx_auth.c auth/arx_auth.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

database/arx_database.o: database/arx_database.c database/arx_database.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

cgo/bridge.o: cgo/bridge.c cgo/bridge.h arxobject/arxobject.h ascii/ascii_engine.h building/arx_building.h version/arx_version.h spatial/arx_spatial.h ingestion/arx_ingestion.h auth/arx_auth.h database/arx_database.h
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

# Test targets
test: test-arxobject test-ascii test-building test-version test-spatial test-ingestion test-wall-composition

test-arxobject: $(LIB_DIR)/$(ARXOBJECT_LIBRARY)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $(TEST_DIR)/test_arxobject.c -L$(LIB_DIR) -larxobject $(LDFLAGS) -o $(TEST_DIR)/test_arxobject
	./$(TEST_DIR)/test_arxobject

test-ascii: $(LIB_DIR)/$(ARXOBJECT_LIBRARY) $(LIB_DIR)/$(ASCII_LIBRARY)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $(TEST_DIR)/test_ascii.c -L$(LIB_DIR) -larxobject -lascii $(LDFLAGS) -o $(TEST_DIR)/test_ascii
	./$(TEST_DIR)/test_ascii

test-building: $(LIB_DIR)/$(ARXOBJECT_LIBRARY) $(LIB_DIR)/$(BUILDING_LIBRARY)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $(TEST_DIR)/test_building.c -L$(LIB_DIR) -larxobject -larxbuilding $(LDFLAGS) -o $(TEST_DIR)/test_building
	./$(TEST_DIR)/test_building

test-version: $(LIB_DIR)/$(ARXOBJECT_LIBRARY) $(LIB_DIR)/$(VERSION_LIBRARY)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $(TEST_DIR)/test_version.c -L$(LIB_DIR) -larxobject -larxversion $(LDFLAGS) -o $(TEST_DIR)/test_version
	./$(TEST_DIR)/test_version

test-spatial: $(LIB_DIR)/$(ARXOBJECT_LIBRARY) $(LIB_DIR)/$(SPATIAL_LIBRARY)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $(TEST_DIR)/test_spatial.c -L$(LIB_DIR) -larxobject -larxspatial $(LDFLAGS) -o $(TEST_DIR)/test_spatial
	./$(TEST_DIR)/test_spatial

test-wall-composition: $(LIB_DIR)/$(WALL_COMPOSITION_LIBRARY)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) wall_composition/test_wall_composition.c -L$(LIB_DIR) -larxwallcomposition $(LDFLAGS) -o wall_composition/test_wall_composition
	./wall_composition/test_wall_composition

# Performance benchmark
benchmark: $(LIB_DIR)/$(ARXOBJECT_LIBRARY) $(LIB_DIR)/$(BUILDING_LIBRARY) $(LIB_DIR)/$(SPATIAL_LIBRARY)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $(TEST_DIR)/benchmark.c -L$(LIB_DIR) -larxobject -larxbuilding -larxspatial $(LDFLAGS) -o $(TEST_DIR)/benchmark
	./$(TEST_DIR)/benchmark

# Clean targets
clean:
	rm -f $(OBJECTS)
	rm -f $(TEST_DIR)/test_*
	rm -f $(TEST_DIR)/benchmark

clean-libs:
	rm -f $(LIB_DIR)/*.a $(LIB_DIR)/*.so

clean-all: clean clean-libs

# Install targets
install: all
	install -d $(DESTDIR)/usr/local/include/arxos
	install -d $(DESTDIR)/usr/local/lib
	install -m 644 arxobject/arxobject.h $(DESTDIR)/usr/local/include/arxos/
	install -m 644 ascii/ascii_engine.h $(DESTDIR)/usr/local/include/arxos/
	install -m 644 building/arx_building.h $(DESTDIR)/usr/local/include/arxos/
	install -m 644 version/arx_version.h $(DESTDIR)/usr/local/include/arxos/
	install -m 644 spatial/arx_spatial.h $(DESTDIR)/usr/local/include/arxos/
	install -m 644 $(LIB_DIR)/*.a $(DESTDIR)/usr/local/lib/
	install -m 644 $(LIB_DIR)/*.so $(DESTDIR)/usr/local/lib/
	ldconfig

uninstall:
	rm -rf $(DESTDIR)/usr/local/include/arxos
	rm -f $(DESTDIR)/usr/local/lib/libarx*.a
	rm -f $(DESTDIR)/usr/local/lib/libarx*.so
	ldconfig

# Development targets
dev: CFLAGS += -DDEBUG -g3 -O0
dev: all

# Release targets
release: CFLAGS += -DNDEBUG -O3 -march=native
release: clean all

# Documentation
docs:
	doxygen Doxyfile

# Help
help:
	@echo "ARXOS C Core Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Build all libraries and shared library"
	@echo "  test         - Run all tests"
	@echo "  benchmark    - Run performance benchmarks"
	@echo "  clean        - Clean object files and test binaries"
	@echo "  clean-libs   - Clean library files"
	@echo "  clean-all    - Clean everything"
	@echo "  install      - Install libraries and headers"
	@echo "  uninstall    - Uninstall libraries and headers"
	@echo "  dev          - Build with debug flags"
	@echo "  release      - Build optimized release version"
	@echo "  docs         - Generate documentation"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Libraries built:"
@echo "  $(ARXOBJECT_LIBRARY) - ArxObject Runtime Engine"
@echo "  $(ASCII_LIBRARY)     - ASCII-BIM Spatial Engine"
@echo "  $(BUILDING_LIBRARY)  - Building Management System"
@echo "  $(VERSION_LIBRARY)   - Version Control System"
@echo "  $(SPATIAL_LIBRARY)   - Spatial Indexing System"
@echo "  $(WALL_COMPOSITION_LIBRARY) - Wall Composition System"
@echo "  $(SHARED_LIB)        - Combined shared library"

.PHONY: all test benchmark clean clean-libs clean-all install uninstall dev release docs help
