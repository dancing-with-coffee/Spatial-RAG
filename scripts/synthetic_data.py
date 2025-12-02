"""
Synthetic Dataset Generator for Spatial-RAG.

Generates realistic spatial documents with:
- Point and Polygon geometries
- Various document types (zoning, permits, traffic, planning)
- Metadata for reranker training (authority_score, recency_days)
"""

import math
import random
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

from shapely.geometry import Point, Polygon, mapping
from shapely.ops import unary_union


@dataclass
class SyntheticDocument:
    """A synthetic spatial document."""

    id: str
    title: str
    content: str
    geometry: dict[str, Any]
    metadata: dict[str, Any]


# Document templates for realistic content
DOCUMENT_TEMPLATES = {
    "zoning": [
        "Zoning classification: {zone_type}. This area permits {permitted_uses}. Maximum building height: {height}m. Setback requirements: {setback}m from property line.",
        "Land use designation: {zone_type} zone. Permitted density: {density} units per hectare. Special conditions apply for {special_conditions}.",
        "Zoning ordinance #{ordinance_num} establishes {zone_type} classification for this parcel. Development must comply with {compliance_requirements}.",
    ],
    "permit": [
        "Building Permit #{permit_num} issued for {project_type}. Project scope: {scope}. Estimated completion: {completion_date}.",
        "Development application #{permit_num} approved for {project_type}. Total floor area: {floor_area} sqm. Conditions: {conditions}.",
        "Construction permit granted for {project_type} at this location. Contractor: {contractor}. Expected duration: {duration} months.",
    ],
    "traffic": [
        "Traffic analysis report: Average daily traffic volume of {volume} vehicles. Peak hour congestion index: {congestion_index}/100. Recommended improvements: {improvements}.",
        "Transportation study findings: {road_type} with capacity for {capacity} vehicles/hour. Current utilization: {utilization}%. Signal timing optimization recommended.",
        "Traffic impact assessment: New development expected to generate {trips} additional trips daily. Mitigation measures: {mitigation}.",
    ],
    "planning": [
        "Urban development plan for {area_name}: Priority areas include {priorities}. Community feedback period ends {feedback_date}.",
        "Master plan update: {area_name} designated for {designation}. Infrastructure investments planned: {investments}.",
        "Strategic planning document: Vision for {area_name} includes {vision}. Implementation timeline: {timeline} years.",
    ],
    "environmental": [
        "Environmental assessment: Site contains {env_feature}. Protection measures required: {protection}. Buffer zone: {buffer}m.",
        "Ecological survey results: {species_count} species identified. Habitat classification: {habitat_class}. Conservation priority: {priority}.",
        "Sustainability report: Green space coverage: {green_coverage}%. Tree canopy target: {canopy_target}%. Biodiversity index: {biodiversity}.",
    ],
    "infrastructure": [
        "Utility infrastructure report: {utility_type} capacity assessment. Current load: {load}%. Upgrade planned for {upgrade_year}.",
        "Public works project: {project_name} to improve {improvement_area}. Budget: ${budget}. Timeline: {timeline}.",
        "Infrastructure inventory: {infrastructure_type} serving {service_area}. Age: {age} years. Condition rating: {condition}/10.",
    ],
}

# Location landmarks for context
LANDMARKS = [
    "Central Business District",
    "University Campus",
    "Industrial Park",
    "Riverside Development",
    "Historic Quarter",
    "Tech Innovation Hub",
    "Medical Center Complex",
    "Sports Stadium Area",
    "Transit Station",
    "Shopping Mall District",
    "Residential Heights",
    "Waterfront Zone",
    "Airport Vicinity",
    "Cultural Center",
    "Green Belt Area",
]

ZONE_TYPES = ["R-1", "R-2", "R-3", "C-1", "C-2", "M-1", "M-2", "MU", "OS", "PD"]


def random_point_around(
    center_lat: float, center_lon: float, max_radius_km: float = 10
) -> Point:
    """Generate random point around a center using uniform angular sampling."""
    radius_deg = max_radius_km / 111.0  # Approximate degrees per km
    r = radius_deg * math.sqrt(random.random())
    theta = random.random() * 2 * math.pi
    lat = center_lat + r * math.cos(theta)
    lon = center_lon + r * math.sin(theta)
    return Point(lon, lat)


def random_polygon_around(
    center_lat: float, center_lon: float, max_radius_km: float = 0.5
) -> Polygon:
    """Generate a small random polygon using convex hull of random points."""
    num_points = random.randint(4, 8)
    points = [
        random_point_around(center_lat, center_lon, max_radius_km)
        for _ in range(num_points)
    ]

    # Create convex hull to ensure valid polygon
    hull = unary_union(points).convex_hull

    if hull.geom_type == "Polygon":
        return hull
    else:
        # Fallback to simple rectangle
        p = random_point_around(center_lat, center_lon, max_radius_km)
        size = max_radius_km / 111.0 * random.uniform(0.1, 0.5)
        return Polygon(
            [
                (p.x - size, p.y - size),
                (p.x + size, p.y - size),
                (p.x + size, p.y + size),
                (p.x - size, p.y + size),
                (p.x - size, p.y - size),
            ]
        )


def generate_document_content(doc_type: str, landmark: str, idx: int) -> str:
    """Generate realistic document content based on type."""
    template = random.choice(
        DOCUMENT_TEMPLATES.get(doc_type, DOCUMENT_TEMPLATES["planning"])
    )

    # Common substitutions
    substitutions = {
        "zone_type": random.choice(ZONE_TYPES),
        "permitted_uses": random.choice(
            ["residential", "commercial", "mixed-use", "industrial", "institutional"]
        ),
        "height": random.randint(10, 100),
        "setback": random.randint(3, 15),
        "density": random.randint(20, 200),
        "special_conditions": random.choice(
            [
                "heritage overlay",
                "flood zone",
                "airport noise contour",
                "environmental sensitivity",
            ]
        ),
        "ordinance_num": f"{random.randint(1000, 9999)}-{random.randint(2020, 2024)}",
        "compliance_requirements": random.choice(
            [
                "design guidelines",
                "environmental standards",
                "accessibility codes",
                "parking requirements",
            ]
        ),
        "permit_num": f"BP-{random.randint(10000, 99999)}",
        "project_type": random.choice(
            [
                "residential tower",
                "commercial complex",
                "mixed-use development",
                "infrastructure upgrade",
                "public facility",
            ]
        ),
        "scope": random.choice(
            ["new construction", "renovation", "expansion", "demolition and rebuild"]
        ),
        "completion_date": (
            datetime.now() + timedelta(days=random.randint(180, 720))
        ).strftime("%B %Y"),
        "floor_area": random.randint(500, 50000),
        "conditions": random.choice(
            [
                "landscaping required",
                "traffic study needed",
                "public consultation",
                "heritage review",
            ]
        ),
        "contractor": f"Builder {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])} Corp",
        "duration": random.randint(6, 36),
        "volume": random.randint(5000, 50000),
        "congestion_index": random.randint(20, 95),
        "improvements": random.choice(
            [
                "signal optimization",
                "lane widening",
                "roundabout installation",
                "pedestrian crossing",
            ]
        ),
        "road_type": random.choice(["arterial", "collector", "local", "highway"]),
        "capacity": random.randint(1000, 5000),
        "utilization": random.randint(40, 95),
        "trips": random.randint(100, 2000),
        "mitigation": random.choice(
            [
                "turn lanes",
                "traffic signals",
                "access management",
                "transit improvements",
            ]
        ),
        "area_name": landmark,
        "priorities": random.choice(
            [
                "affordable housing",
                "green infrastructure",
                "transit-oriented development",
                "economic revitalization",
            ]
        ),
        "feedback_date": (
            datetime.now() + timedelta(days=random.randint(30, 90))
        ).strftime("%B %d, %Y"),
        "designation": random.choice(
            [
                "growth center",
                "conservation area",
                "innovation district",
                "heritage precinct",
            ]
        ),
        "investments": random.choice(
            [
                "transit extension",
                "park improvements",
                "utility upgrades",
                "road reconstruction",
            ]
        ),
        "vision": random.choice(
            [
                "sustainable community",
                "walkable neighborhood",
                "economic hub",
                "cultural destination",
            ]
        ),
        "timeline": random.randint(5, 20),
        "env_feature": random.choice(
            ["wetland area", "mature tree stand", "wildlife corridor", "riparian zone"]
        ),
        "protection": random.choice(
            [
                "buffer zone",
                "stormwater management",
                "erosion control",
                "habitat restoration",
            ]
        ),
        "buffer": random.randint(15, 100),
        "species_count": random.randint(10, 150),
        "habitat_class": random.choice(["Category A", "Category B", "Category C"]),
        "priority": random.choice(["High", "Medium", "Low"]),
        "green_coverage": random.randint(15, 45),
        "canopy_target": random.randint(25, 50),
        "biodiversity": round(random.uniform(0.3, 0.9), 2),
        "utility_type": random.choice(
            ["water", "sewer", "stormwater", "electrical", "gas"]
        ),
        "load": random.randint(50, 95),
        "upgrade_year": random.randint(2025, 2030),
        "project_name": f"Project {random.choice(['Phoenix', 'Horizon', 'Gateway', 'Cornerstone'])}",
        "improvement_area": random.choice(
            ["drainage", "pedestrian safety", "accessibility", "capacity"]
        ),
        "budget": f"{random.randint(1, 50)},{random.randint(100, 999)},{random.randint(100, 999)}",
        "infrastructure_type": random.choice(
            ["water main", "sewer line", "road segment", "bridge"]
        ),
        "service_area": f"{random.randint(500, 5000)} properties",
        "age": random.randint(10, 80),
        "condition": random.randint(3, 10),
    }

    try:
        return template.format(**substitutions)
    except KeyError:
        # Fallback if template has unknown keys
        return f"Spatial document {idx} for {landmark}. Type: {doc_type}. Contains planning and regulatory information for this location."


def generate_synthetic_documents(
    n: int = 1000,
    center_lat: float = 31.5204,  # Lahore, Pakistan
    center_lon: float = 74.3587,
    city: str = "Lahore",
    polygon_ratio: float = 0.3,
) -> list[SyntheticDocument]:
    """
    Generate synthetic spatial documents.

    Args:
        n: Number of documents to generate
        center_lat: Center latitude for document locations
        center_lon: Center longitude for document locations
        city: City name for metadata
        polygon_ratio: Ratio of polygon geometries (vs points)

    Returns:
        List of SyntheticDocument objects
    """
    documents = []
    doc_types = list(DOCUMENT_TEMPLATES.keys())

    for i in range(n):
        doc_id = str(uuid.uuid4())
        doc_type = random.choice(doc_types)
        landmark = random.choice(LANDMARKS)

        # Generate geometry
        if random.random() < polygon_ratio:
            geom = random_polygon_around(center_lat, center_lon)
        else:
            geom = random_point_around(center_lat, center_lon)

        # Generate content
        content = generate_document_content(doc_type, landmark, i)

        # Generate metadata with features for reranker
        days_old = random.randint(0, 1500)
        metadata = {
            "city": city,
            "landmark": landmark,
            "doc_type": doc_type,
            "authority_score": round(random.uniform(0.3, 1.0), 3),
            "recency_days": days_old,
            "source": random.choice(
                [
                    "city_planning",
                    "public_records",
                    "environmental_agency",
                    "transport_authority",
                ]
            ),
            "created_at": (datetime.utcnow() - timedelta(days=days_old)).isoformat(),
            "verified": random.random() > 0.2,  # 80% verified
        }

        doc = SyntheticDocument(
            id=doc_id,
            title=f"{doc_type.capitalize()} Report - {landmark} #{i+1}",
            content=content,
            geometry=mapping(geom),
            metadata=metadata,
        )
        documents.append(doc)

    return documents


def documents_to_geojson(documents: list[SyntheticDocument]) -> dict:
    """Convert documents to GeoJSON FeatureCollection."""
    features = []
    for doc in documents:
        feature = {
            "type": "Feature",
            "geometry": doc.geometry,
            "properties": {
                "id": doc.id,
                "title": doc.title,
                "content": (
                    doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                ),
                **doc.metadata,
            },
        }
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


if __name__ == "__main__":
    import json

    print("Generating 1000 synthetic documents...")
    docs = generate_synthetic_documents(n=1000)

    print(f"Generated {len(docs)} documents")
    print(f"Document types: {set(d.metadata['doc_type'] for d in docs)}")

    # Export to GeoJSON for visualization
    geojson = documents_to_geojson(docs)
    with open("synthetic_dataset.geojson", "w") as f:
        json.dump(geojson, f, indent=2)

    print("Saved to synthetic_dataset.geojson")

    # Print sample document
    print("\nSample document:")
    sample = docs[0]
    print(f"  ID: {sample.id}")
    print(f"  Title: {sample.title}")
    print(f"  Content: {sample.content[:100]}...")
    print(f"  Geometry type: {sample.geometry['type']}")
    print(f"  Metadata: {sample.metadata}")
