use arxos::core::{Building, Floor, Room, RoomType};
use arxos::ifc::IFCProcessor;
use arxos::ifc::parser::lexer::{RawEntity, Param};
use arxos::ifc::parser::registry::EntityRegistry;
use arxos::ifc::parser::geometry::{GeometryResolver, Transform3D};
use arxos::ifc::parser::mesh::MeshResolver;
use arxos::export::ifc::IFCExporter;
use arxos::yaml::BuildingData;
use nalgebra::Matrix4;
use tempfile::NamedTempFile;
use anyhow::Result;

#[test]
fn test_native_geometry_resolution() {
    let mut registry = EntityRegistry::new();
    
    // Triangle points
    registry.register(RawEntity { id: 1, class: "IFCCARTESIANPOINT".to_string(), params: vec![Param::List(vec![Param::Float(0.0), Param::Float(0.0), Param::Float(0.0)])] });
    registry.register(RawEntity { id: 2, class: "IFCCARTESIANPOINT".to_string(), params: vec![Param::List(vec![Param::Float(1.0), Param::Float(0.0), Param::Float(0.0)])] });
    registry.register(RawEntity { id: 3, class: "IFCCARTESIANPOINT".to_string(), params: vec![Param::List(vec![Param::Float(0.0), Param::Float(1.0), Param::Float(0.0)])] });
    
    registry.register(RawEntity { id: 10, class: "IFCPOLYLOOP".to_string(), params: vec![Param::List(vec![Param::Reference(1), Param::Reference(2), Param::Reference(3)])] });
    registry.register(RawEntity { id: 11, class: "IFCFACEOUTERBOUND".to_string(), params: vec![Param::Reference(10), Param::Boolean(true)] });
    registry.register(RawEntity { id: 12, class: "IFCFACE".to_string(), params: vec![Param::List(vec![Param::Reference(11)])] });
    registry.register(RawEntity { id: 13, class: "IFCCLOSEDSHELL".to_string(), params: vec![Param::List(vec![Param::Reference(12)])] });
    registry.register(RawEntity { id: 100, class: "IFCFACETEDBREP".to_string(), params: vec![Param::Reference(13)] });

    let geometry = GeometryResolver::new(&registry);
    let mesh_resolver = MeshResolver::new(&registry, &geometry);
    let transform = Transform3D { matrix: Matrix4::identity() };

    let mesh = mesh_resolver.resolve_mesh_item(100, &transform).expect("Should resolve mesh");
    assert_eq!(mesh.vertices.len(), 3);
}

#[test]
fn test_ifc_export_with_properties() -> Result<()> {
    let mut building = Building::new("Prop Building".to_string(), "/prop".to_string());
    building.add_metadata_property("building_status".to_string(), "active".to_string());

    let mut floor = Floor::new("Level 1".to_string(), 1);
    floor.properties.insert("fire_rating".to_string(), "2h".to_string());
    
    let mut room = Room::new("Server Room".to_string(), RoomType::Mechanical);
    room.properties.insert("cooling_load".to_string(), "5kW".to_string());
    
    let mut wing = arxos::core::Wing::new("Main".to_string());
    wing.add_room(room);
    floor.add_wing(wing);
    building.add_floor(floor);

    let data = BuildingData { building, equipment: vec![] };
    let file = NamedTempFile::new()?;
    let exporter = IFCExporter::new(data);
    exporter.export(file.path())?;

    let content = std::fs::read_to_string(file.path())?;
    assert!(content.contains("IFCPROPERTYSET"));
    assert!(content.contains("fire_rating"));
    assert!(content.contains("active"));
    assert!(content.contains("5kW"));
    
    Ok(())
}

#[test]
fn test_native_validation_strict() -> Result<()> {
    let content = "ISO-10303-21;
DATA;
#1= IFCPROJECT('guid', $, 'name', $, $, $, $, (#2), #3);
#2= IFCGEOMETRICREPRESENTATIONCONTEXT($, 'Model', 3, 1.E-05, #10, $);
#3= IFCUNITASSIGNMENT((#11));
ENDSEC;
END-ISO-10303-21;";

    let file = NamedTempFile::new()?;
    std::fs::write(file.path(), content)?;

    let processor = IFCProcessor::new();
    // Strict validation should fail because there is no Building/Floor/Site
    let result = processor.parse_native(file.path().to_str().unwrap(), true);
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("No spatial entities found"));

    Ok(())
}
